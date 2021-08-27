# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaparserItem(scrapy.Item):
    # define the fields for your item here like:
    _id = scrapy.Field()
    follow_list = scrapy.Field()
    fol_username = scrapy.Field()
    fol_user_id = scrapy.Field()
    pic_url = scrapy.Field()
    j_body = scrapy.Field()
    username = scrapy.Field()
    user_id = scrapy.Field()
