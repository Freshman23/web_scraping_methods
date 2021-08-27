from pymongo import MongoClient
from pprint import pprint

query = input('Enter the considered username and fol_list separated by a comma:\n')
# for example,
# query = 'username123, followers'
user, fol_list = query.split(',')

client = MongoClient('localhost', 27017)
mongo_base = client['instacom']
collection = mongo_base[user.strip()]

num = 0
for user in collection.find({'follow_list': fol_list.strip()},
                            {'_id': 0, 'fol_username': 1}):
    num += 1
    pprint([num, user])
