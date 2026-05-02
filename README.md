Scrape sunnah.com for their changes
Database for entries?

Hadith could have
  Name of Collection
  Description

Languages
  Name

Entry could have
  Narrator
  Corpus
  link to Hadith
  link to language
  last_updated

Part of .english_hadith_full
.hadith_narrated
.text_details

Part of .arabic_hadith_full
.arabic_text_details


Wayback machine scraper
Middleware that automatically deals with contacting the api (https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md) they have a cdx server that hosts the index used to look up snapshots.
Since we're going to be parsing the response... seems like a good idea to use ScrapyWaybackMachine https://github.com/sangaline/scrapy-wayback-machine
Looks like it uses a python library called Scrapy.  Not sure how that compares to beautiful soup.

Use scrapy as a spider

https://archive.org/help/wayback_api.php
https://docs.scrapy.org/en/latest/
https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
https://archive.org/donate/
https://github.com/sangaline/scrapy-wayback-machine