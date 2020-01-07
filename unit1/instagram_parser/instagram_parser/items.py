# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UserItem(scrapy.Item):
    _id = scrapy.Field()
    user_id = scrapy.Field()
    username = scrapy.Field()
    full_name = scrapy.Field()


class FollowingItem(scrapy.Item):
    _id = scrapy.Field()
    user_id = scrapy.Field()
    followers = scrapy.Field()

