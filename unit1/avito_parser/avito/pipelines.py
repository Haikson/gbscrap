# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


class AvitoPipeline(object):
    def process_item(self, item, spider):
        mongo_collection = MongoCollection(collection_name=type(item).__name__)
        mongo_collection.insert(item)
        return item
