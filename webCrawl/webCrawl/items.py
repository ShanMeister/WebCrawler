# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WebcrawlItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    org_name = scrapy.Field()
    subject = scrapy.Field()
    method = scrapy.Field()
    category = scrapy.Field()
    declare_date = scrapy.Field()
    deadline = scrapy.Field()
    budget = scrapy.Field()
    url = scrapy.Field()
    last_updated = scrapy.Field(serializer=str)
