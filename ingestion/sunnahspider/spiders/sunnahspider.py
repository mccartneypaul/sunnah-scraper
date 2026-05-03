from pathlib import Path
from datetime import datetime

import scrapy

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
        self.log(f"Saved file {filepath}")

# Fill out the model for the hadith data
# Hadith narrator = response.css("div.hadithTextContainers .english_hadith_full *::text")
# Hadith text = response.css("div.hadithTextContainers .english_hadith_full .text_details *::text")
# Hadith grade = 'Sahih' if we're pulling from Bukhari
# More grade (need to check if this works): response.xpath("normalize-space(//td[b[contains(normalize-space(.), 'Grade')]]/following-sibling::td[1])").get()
# Hadith language = 'en'
# Hadith collection = 'Sahih Bukhari'
# Hadith link = response.css("table.hadith_reference a::attr(href)")
# Hadith reference number = response.css("table.hadith_reference a::text").re_first(r'\d+')
# Hadith in book reference = response.xpath("normalize-space(//table[contains(concat(' ', normalize-space(@class), ' '), ' hadith_reference ')]//tr[td[1][contains(normalize-space(.), 'In-book reference')]]/td[2])")
