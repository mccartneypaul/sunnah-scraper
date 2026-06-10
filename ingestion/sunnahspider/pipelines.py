# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
import django
from asgiref.sync import sync_to_async
from django.db import transaction

class DjangoHadithPipeline:
    def __init__(self):
        self.Collection = None
        self.Language = None
        self.Snapshot = None
        self.Hadith = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls()
    
    def _setup_django(self):
        project_root = Path(__file__).resolve().parents[2]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trackersite.settings")

        django.setup()

    def open_spider(self):
        self._setup_django()
        from corpus.models import Collection, Language, Snapshot, Hadith
        self.Collection = Collection
        self.Language = Language
        self.Snapshot = Snapshot
        self.Hadith = Hadith

    async def process_item(self, item):
        # Scrapy can run pipelines in an async context; keep Django ORM in a sync thread.
        return await sync_to_async(self._process_item_sync, thread_sensitive=True)(item)

    def _process_item_sync(self, item):
        if not self.Collection or not self.Language or not self.Snapshot or not self.Hadith:
            raise DropItem("Django models not set up properly in pipeline")

        data = ItemAdapter(item).asdict()

        with transaction.atomic():
            # First, create a snapshot that represents the point-in-time of this data ingestion.
            snapshot, _ = self.Snapshot.objects.get_or_create(
                taken_on=data.get("snapshot_date", datetime.now(timezone.utc)),
                source=data.get("snapshot_source", "unknown").strip(),
            )

            # Retrieve the collection
            collection = self.Collection.objects.filter(
                name=data["collection_name"].strip()
            ).first()

            if not collection:
                raise DropItem(f"Collection '{data['collection_name']}' not found in database")

            hadith_list = data["base_hadith_list"] = data.get("base_hadith_list", [])
            
            # Get a list of all languages so we can look them up by ISO code
            languages = self.Language.objects.all()

            for hadith_data in hadith_list:
                language_obj = languages.filter(iso_two_code=hadith_data.get("language_iso_two_code")).first()
                reference_number = int(hadith_data.get("reference_number", 0))
                
                if reference_number == 0:
                    raise DropItem("Hadith missing reference_number or reference_number is not an integer for hadith at link: {}".format(hadith_data.get("link")))

                self.Hadith.objects.create(
                    snapshot=snapshot,
                    collection=collection,
                    language=language_obj,
                    reference_number=reference_number,
                    in_book_reference=(hadith_data.get("book_reference_number") or "").strip(),
                    narrator=(hadith_data.get("narrator") or "").strip(),
                    text=(hadith_data.get("text") or "").strip(),
                    grade=(hadith_data.get("grade") or "").strip(),
                    link=(hadith_data.get("link") or "").strip(),
                )

        return item