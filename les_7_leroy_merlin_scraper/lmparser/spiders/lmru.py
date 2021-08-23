import scrapy
from scrapy.http import HtmlResponse
from lmparser.items import LmparserItem
from scrapy.loader import ItemLoader


class LmruSpider(scrapy.Spider):
    name = 'lmru'
    allowed_domains = ['leroymerlin.ru']

    def __init__(self, search):
        super().__init__()
        self.search = search
        self.start_urls = [f'https://leroymerlin.ru/catalogue/{search}/']

    def parse(self, response: HtmlResponse, **kwargs):
        next_page = response.xpath("//a[@data-qa-pagination-item='right']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        links = response.xpath("//a[@data-qa='product-image']")
        for link in links:
            yield response.follow(link, callback=self.good_parse)

    def good_parse(self, response: HtmlResponse):
        loader = ItemLoader(item=LmparserItem(), response=response)
        loader.add_value('link', response.url)
        loader.add_xpath('title', "//h1/text()")
        loader.add_xpath('price', "//span[@slot='price']/text()")
        loader.add_xpath('photos', "//source[contains(@media,'(min-width: 1024px)')]/@srcset")
        loader.add_xpath('chars', "//uc-pdp-section-vlimited//*[self::dt or self::dd]/text()")

        yield loader.load_item()
