from pymongo import MongoClient

import threading

class SingletonMixin(object):
    __singleton_lock = threading.Lock()
    __singleton_instance = None

    @classmethod
    def instance(cls):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = cls()
        return cls.__singleton_instance

class MongoConnection(SingletonMixin):

    def __init__(self, host='localhost', port=27017, collection_name="avito"):
        mongo_client = MongoClient(host, port)
        self.db = mongo_client['gb_scrap']
        self.user_collection = self.db['instagram_user']
        self.follower_collection = self.db['instagram_follower']

    def clear_mongo_collection(self):
        self.mongo_collection.delete_many({})
