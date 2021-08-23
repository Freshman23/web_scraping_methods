# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient
import scrapy
import os


class LmparserPipeline:
    def __init__(self):
        self.client = MongoClient('localhost', 27017)

    def process_chars(self, chars: list) -> dict:
        chars_dict = {}

        for i, ch in enumerate(chars[1::2]):
            try:
                ch = int(ch)
            except ValueError:
                try:
                    ch = float(ch)
                except ValueError:
                    pass

            chars_dict[chars[i * 2]] = ch

        return chars_dict

    def process_item(self, item, spider):
        item['chars'] = self.process_chars(item['chars'])

        mongo_base = self.client[spider.name]
        collection = mongo_base[spider.search]
        collection.insert_one(item)

        return item


class LmImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['photos']:
            for img in item['photos']:
                try:
                    yield scrapy.Request(img)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        if results:
            item['photos'] = [itm[1] for itm in results if itm[0]]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        filename = os.path.basename(request.url)
        filedir = os.path.basename(item['link'][:-1])
        return f'full/{filedir}/{filename}'
