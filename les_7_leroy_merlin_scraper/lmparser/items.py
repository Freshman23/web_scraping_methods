# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import MapCompose, TakeFirst


class LmparserItem(scrapy.Item):
    _id = scrapy.Field()
    link = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(input_processor=MapCompose(lambda prc: int(prc.replace(' ', ''))),
                         output_processor=TakeFirst())
    photos = scrapy.Field()
    chars = scrapy.Field(input_processor=MapCompose(lambda char: char.strip()))
