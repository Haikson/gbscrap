from pymongo import MongoClient


class MongoCollection(object):

    def __init__(self, host='localhost', port=27017, collection_name="avito"):
        mongo_client = MongoClient(host, port)
        self.db = mongo_client['gb_scrap']
        self.mongo_collection = self.db[collection_name]

    def clear_mongo_collection(self):
        self.mongo_collection.delete_many({})
