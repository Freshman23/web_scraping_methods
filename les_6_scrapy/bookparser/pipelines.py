# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class BookparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client['books']

    def process_item(self, item, spider):

        if spider.name == 'labru':
            item['authors'] = item['authors'] if item['authors'] else None
            item['price_old'] = int(item['price_old']) if item['price_old'] else None
            item['price_new'] = int(item['price_new']) if item['price_new'] else None
            item['rate'] = float(item['rate']) if float(item['rate']) else None

        elif spider.name == 'b24ru':
            item['title'] = item['title'].strip()
            item['authors'] = [auth.strip() for auth in item['authors']] if item['authors'] else None
            item['price_old'] = item['price_old'].strip() if item['price_old'] else None
            item['price_new'] = item['price_new'].strip() if item['price_new'] else None
            item['rate'] = float(item['rate'].strip().replace(',', '.')) if item['rate'].strip() != '0,0' else None

        collection = self.mongo_base[spider.name]
        collection.insert_one(item)

        return item
