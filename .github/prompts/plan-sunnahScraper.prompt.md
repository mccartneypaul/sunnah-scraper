## Plan: Persist Scraped Hadith Into Django

Wire Scrapy to Django via a dedicated item pipeline that initializes Django, creates one Snapshot per spider run, and upserts Hadith rows keyed by snapshot+collection+language+reference number while keeping raw HTML snapshot files on disk. This follows Scrapy conventions (extract in spider, persist in pipeline) and supports historical change tracking.

**Steps**

1. Phase 1: Normalize hadith extraction into an item contract.
2. Add/confirm a Scrapy Item schema in `/Users/lucis/code/src/SunnahScraper/ingestion/sunnahspider/items.py` for normalized hadith payload fields used by DB persistence: `collection_name`, `language_iso`, `language_name`, `reference_number`, `in_book_reference`, `narrator`, `text`, `grade`, `link`, `source`, plus run metadata.
3. Update spider extraction in `/Users/lucis/code/src/SunnahScraper/ingestion/sunnahspider/spiders/sunnahspider.py` so `parse` continues writing raw HTML files and `parse_hadith` yields one normalized item per hadith with the minimal shape below:

   ```python
   {
	   "collection_name": "Sahih Bukhari",
	   "language_iso": "en",
	   "language_name": "English",
	   "reference_number": 1,
	   "in_book_reference": "Book 1, Hadith 1",
	   "narrator": "Narrated ...",
	   "text": "...",
	   "grade": "Sahih",
	   "link": "https://sunnah.com/bukhari/1",
	   "source": "sunnah.com",
	   "run_timestamp": timestamp,
   }
   ```
4. Ensure one run-level timestamp/run-id is generated in spider start and propagated via `response.meta` so all items in that crawl are attached to the same Snapshot. _Blocks step 6._
5. Phase 2: Django pipeline persistence.
6. Implement `DjangoHadithPipeline` in `/Users/lucis/code/src/SunnahScraper/ingestion/sunnahspider/pipelines.py` that bootstraps Django (`DJANGO_SETTINGS_MODULE=trackersite.settings`, `django.setup()`), lazily imports `Collection`, `Language`, `Snapshot`, and `Hadith`, and wraps writes in `transaction.atomic`.
7. In pipeline `open_spider`, create/fetch exactly one Snapshot for the run using the run timestamp/source metadata, cache it on the pipeline instance, and reuse it in `process_item`.
8. In `process_item`, resolve FKs with `get_or_create` (`Collection` by name, `Language` by iso code with name default), then persist Hadith with `update_or_create` keyed by `(snapshot, collection, language, reference_number)` and defaults for mutable text fields.
9. Add robust validation/conversion in pipeline (int conversion for `reference_number`, nullable handling for optional fields, link normalization) and `DropItem` on non-recoverable malformed payloads. _Parallel with step 8 once skeleton exists._
10. Phase 3: Scrapy settings + model constraints.
11. Configure `/Users/lucis/code/src/SunnahScraper/ingestion/sunnahspider/settings.py` to enable `ITEM_PIPELINES` with the Django pipeline and ensure project root import path is available to resolve `trackersite.settings` and `corpus.models`.
12. Add DB-level uniqueness in `/Users/lucis/code/src/SunnahScraper/corpus/models.py` on `Hadith` with a `UniqueConstraint` over `snapshot`, `collection`, `language`, `reference_number` to enforce the history model in schema. _Blocks step 13._
13. Generate and apply migration under `/Users/lucis/code/src/SunnahScraper/corpus/migrations/` for the new uniqueness constraint.
14. Phase 4: Verification.
15. Run migrations, execute a limited spider crawl, and verify row creation for Collection/Language/Snapshot/Hadith plus snapshot file output. Re-run crawl with same run-id behavior expectations to confirm `update_or_create` idempotency within a run and new rows for a new run snapshot.

**Relevant files**

- `/Users/lucis/code/src/SunnahScraper/ingestion/sunnahspider/spiders/sunnahspider.py` — keep raw HTML archiving, emit normalized hadith items, propagate run metadata.
- `/Users/lucis/code/src/SunnahScraper/ingestion/sunnahspider/items.py` — define item contract used between spider and pipeline.
- `/Users/lucis/code/src/SunnahScraper/ingestion/sunnahspider/pipelines.py` — implement Django bootstrap + FK resolution + atomic upsert logic.
- `/Users/lucis/code/src/SunnahScraper/ingestion/sunnahspider/settings.py` — enable pipeline and integration settings.
- `/Users/lucis/code/src/SunnahScraper/corpus/models.py` — enforce uniqueness constraint aligned with your selected historical model.
- `/Users/lucis/code/src/SunnahScraper/corpus/migrations/` — migration for schema constraint.

**Verification**

1. Run `python manage.py makemigrations corpus` and `python manage.py migrate` with no errors.
2. Run spider (`scrapy crawl sunnah`) and check logs for pipeline writes and no FK/validation exceptions.
3. Query DB via Django shell to verify one Snapshot for the run and Hadith rows linked to that snapshot.
4. Confirm raw files still written under `ingestion/sunnahspider/snapshots/...`.
5. Re-run crawl with a new run timestamp and verify a new Snapshot is created and Hadith history is preserved across snapshots.

**Decisions**

- Uniqueness rule: `(snapshot, collection, language, reference_number)`.
- Snapshot granularity: one Snapshot per spider run.
- Raw HTML retention: keep on-disk snapshots for future reference display.
- In scope: Scrapy-to-Django persistence path, model constraint, and verification.
- Out of scope: UI/API to display snapshots, backfilling old raw snapshot directories, and advanced crawl scheduling.

**Further Considerations**

1. Snapshot identity policy recommendation: use explicit run UUID + UTC `taken_on` to avoid accidental coalescing when two crawls start in the same second.
2. Extraction resilience recommendation: add selector fallback paths and counters for missing narrator/reference fields to reduce dropped items during site markup drift.
3. Operational recommendation: add lightweight crawl stats logging (items scraped, saved, dropped) to support monitoring before adding full task orchestration.
