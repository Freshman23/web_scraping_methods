# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class InstaparserPipeline:
    def __init__(self):
        self.client = MongoClient('localhost', 27017)

    def process_item(self, item, spider):
        mongo_base = self.client[spider.name]
        collection = mongo_base[item.get('username')]
        collection.insert_one(item)

        return item
