import pymongo
from pymongo import MongoClient
from pymongo import errors

class Mongo:
    def __init__(self):
        self.cluster = MongoClient('')
        db = self.cluster['DB']
        self.collection = db['Stories']
