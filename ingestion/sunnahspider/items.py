# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BaseHadith(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    hadith_narrator = scrapy.Field()
    hadith_paragraphs = scrapy.Field()
    hadith_text = scrapy.Field()
    hadith_grade = scrapy.Field()
    hadith_language = scrapy.Field()
    hadith_link = scrapy.Field()
    hadith_reference_number = scrapy.Field()
    hadith_book_reference_number = scrapy.Field()
    pass

class Hadith(scrapy.Item):
    collection_name = scrapy.Field()
    base_hadith_list = scrapy.Field()
    snapshot_source = scrapy.Field() 
    snapshot_date = scrapy.Field()
    pass
