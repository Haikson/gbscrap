# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HhItem(scrapy.Item):
    _id = scrapy.Field()
    title = scrapy.Field()
    salary_from = scrapy.Field()
    salary_to = scrapy.Field()
    salary_cur = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    company_url = scrapy.Field()
    company_name = scrapy.Field()
    skills = scrapy.Field()
