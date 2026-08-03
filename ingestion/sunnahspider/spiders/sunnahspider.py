from pathlib import Path
from datetime import datetime
import json
from django.utils import timezone

import scrapy
from scrapy.exceptions import CloseSpider

from sunnahspider.items import BaseHadith

class SunnahSpider(scrapy.Spider):
    name = "sunnah"

    async def start(self):
        # Prefer a static URL manifest instead of discovering by crawling.
        timestamp = timezone.now()
        config_path = self.get_collections_path()
        collections = self.load_collections(config_path)

        for collection_name, urls in collections.items():
            for url in urls:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    meta={
                        "collection": collection_name,
                        "source": "sunnah.com",
                        "timestamp": timestamp,
                    },
                )

    def get_collections_path(self) -> Path:
        cli_path = getattr(self, "collections_file", None)
        if cli_path:
            path = Path(cli_path)
            return path if path.is_absolute() else (Path.cwd() / path)

        # Default to the package-level JSON file.
        return Path(__file__).resolve().parents[1] / "collections.json"

    def load_collections(self, config_path: Path) -> dict[str, list[str]]:
        if not config_path.exists():
            raise CloseSpider(
                f"Collections file not found: {config_path}. "
                "Provide one with -a collections_file=<path> or create ingestion/sunnahspider/collections.json"
            )

        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CloseSpider(f"Invalid JSON in collections file {config_path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise CloseSpider(
                "Collections JSON must be an object mapping collection names to URL lists."
            )

        collections: dict[str, list[str]] = {}
        for collection_name, urls in raw.items():
            if not isinstance(collection_name, str) or not collection_name.strip():
                raise CloseSpider("Each collection key must be a non-empty string.")

            if not isinstance(urls, list) or not all(isinstance(url, str) for url in urls):
                raise CloseSpider(
                    f"Collection '{collection_name}' must map to a list of URL strings."
                )

            collections[collection_name.strip()] = [url.strip() for url in urls if url.strip()]

        if not collections:
            raise CloseSpider("Collections JSON did not contain any URLs to crawl.")

        return collections

    def parse(self, response):
        collection = response.meta.get("collection", "unknown")
        source = response.meta.get("source", "unknown")
        timestamp = response.meta.get("timestamp", "unknown")

        page = response.url.split("/")[-1]
        snapshot_dir = Path(f"sunnahspider/snapshots/{source}_{timestamp.strftime('%Y%m%d_%H%M%S')}/{collection}")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        filepath = snapshot_dir / f"{page}.html"
        filepath.write_bytes(response.body)
        self.logger.info(f"Saved file {filepath}")

        hadith_list = list(self.parse_hadith_chapter(response))
        yield {
            "collection_name": collection,
            "base_hadith_list": hadith_list,
            "snapshot_source": source,
            "snapshot_date": timestamp,
        }

    def parse_hadith_chapter(self, response):
        raw_hadith_list = response.css("div.actualHadithContainer")

        self.logger.info(f"Found {len(raw_hadith_list)} hadith in chapter page {response.url}")
        
        # Delegate extraction of each hadith block to parse_hadith.
        for raw_hadith in raw_hadith_list:
            yield self.parse_hadith(raw_hadith, response)

    def parse_hadith(self, raw_hadith, response):
        hadith_narrator_parts = raw_hadith.css(
            ".english_hadith_full .hadith_narrated *::text"
        ).getall()
        hadith_narrator = " ".join(part.strip() for part in hadith_narrator_parts if part.strip())

        paragraphs = raw_hadith.css(".english_hadith_full .text_details p").xpath(
            "normalize-space(string(.))"
        ).getall()
        hadith_paragraphs = [paragraph for paragraph in paragraphs if paragraph]
        hadith_text = "\n\n".join(hadith_paragraphs)

        return BaseHadith(
            narrator=hadith_narrator,
            paragraphs=hadith_paragraphs,
            text=hadith_text,
            grade="Sahih" if "bukhari" in response.url else None,
            language_iso_two_code="en",
            link=raw_hadith.css(".hadith_reference a::attr(href)").get(),
            reference_number=raw_hadith.css("table.hadith_reference a::text").re_first(r"\d+"),
            book_reference_number=raw_hadith.xpath(
                "normalize-space(.//table[contains(concat(' ', normalize-space(@class), ' '), ' hadith_reference ')]"
                "//tr[td[1][contains(normalize-space(.), 'In-book reference')]]/td[2])"
            ).get(),
        )

