# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SuningItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    price = scrapy.Field()
    name = scrapy.Field()
    b_type = scrapy.Field()
    m_type = scrapy.Field()
    s_type = scrapy.Field()
    url = scrapy.Field()

