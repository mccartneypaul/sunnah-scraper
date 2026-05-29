from pathlib import Path
from datetime import datetime

import scrapy

from sunnahspider.items import BaseHadith

class SunnahSpider(scrapy.Spider):
    name = "sunnah"

    async def start(self):
        # Might list all urls here and yield them, or read them from a file, or generate them.
        # Prefer not to generate from crawling for the web demand...
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        urls = [
            "https://sunnah.com/bukhari/1",
            "https://sunnah.com/bukhari/2",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={"collection": "bukhari", "source": "sunnah.com", "timestamp": timestamp})

    def parse(self, response):
        collection = response.meta.get("collection", "unknown")
        source = response.meta.get("source", "unknown")
        timestamp = response.meta.get("timestamp", "unknown")

        page = response.url.split("/")[-1]
        snapshot_dir = Path(f"sunnahspider/snapshots/{source}_{timestamp}/{collection}")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        filepath = snapshot_dir / f"{page}.html"
        filepath.write_bytes(response.body)
        self.logger.info(f"Saved file {filepath}")

        # TODO: Annotate the list of hadith that are returned with the snapshot infor and collection data
        yield from self.parse_hadith_chapter(response)

# Could probably create a separate function to work on the html that was pulled down.

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
            hadith_narrator=hadith_narrator,
            hadith_paragraphs=hadith_paragraphs,
            hadith_text=hadith_text,
            hadith_grade="Sahih" if "bukhari" in response.url else None,
            hadith_language="en",
            hadith_link=raw_hadith.css(".hadith_reference a::attr(href)").get(),
            hadith_reference_number=raw_hadith.css("table.hadith_reference a::text").re_first(r"\d+"),
            hadith_book_reference_number=raw_hadith.xpath(
                "normalize-space(.//table[contains(concat(' ', normalize-space(@class), ' '), ' hadith_reference ')]"
                "//tr[td[1][contains(normalize-space(.), 'In-book reference')]]/td[2])"
            ).get(),
        )

