import os
import pymongo

MongoUser = os.getenv('MongoUser')
MongoPass = os.getenv('MongoPass')
MongoPublicIP = os.getenv('MongoPublicIP')
print(MongoUser, MongoPass, MongoPublicIP)

client = pymongo.MongoClient(f'mongodb://{MongoUser}:{MongoPass}@localhost/cool_db') # defaults to port 27017

db = client.cool_db

# print the number of documents in a collection
print(db.cool_collection.count())
