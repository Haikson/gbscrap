# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request
from instagram_parser.db import MongoConnection
from instagram_parser.items import FollowingItem, UserItem


class InstagramParserPipeline(object):
    def get_or_create_user(self, **conditions):
        user_collection = MongoConnection().user_collection
        user = user_collection.find(
            {
                "$or": [
                    {key: val} for key, val in conditions.items()
                ]
            }
        )
        if user.count() == 0:
            user_collection.insert_one(conditions)
        else:
            user_collection.update_one(
                {
                    "$or": [
                        {key: val} for key, val in conditions.items()
                    ]
                },
                {"$set": conditions}
            )
        return user_collection.find(conditions).next()

    def process_item(self, item, spider):
        if isinstance(item, FollowingItem):
            follower_collection = MongoConnection().follower_collection

            user = self.get_or_create_user(user_id=item["user_id"])
            follower = self.get_or_create_user(user_id=item["followers"][0])
            if follower_collection.count_documents(filter={'user_id': user["_id"]}):
                follower_object = follower_collection.find({'user_id': user["_id"]}).next()
                if follower["_id"] not in follower_object["followers"]:
                    follower_object["followers"].append(follower["_id"])
                    follower_collection.update(
                        {'user_id': user["_id"]},
                        {"$set": {"followers": follower_object["followers"]}}
                    )
                item.update(follower_object)
            else:
                item.update({"user_id": user["_id"], "followers": [follower["_id"]]})
                follower_collection.insert(item)

        elif isinstance(item, UserItem):
            user_collection = MongoConnection().user_collection
            if user_collection.count_documents(filter={'username': item["username"]}) == 0:
                user_collection.insert(item)
            else:
                user_collection.update({"username": item["username"]}, {"$set": item})

        return item


# class PhotoDownloaderPipeline(ImagesPipeline):
#     def get_media_requests(self, item, info):
#         if item.get('photos'):
#             for photo in item.get('photos'):
#                 try:
#                     yield Request(photo)
#                 except Exception as e:
#                     print(e)
#
#         return item
#
#     def item_completed(self, results, item, info):
#         if results:
#             item['photos'] = [itm[1] for itm in results]
