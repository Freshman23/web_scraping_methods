import scrapy
from scrapy.http import HtmlResponse
from bookparser.items import BookparserItem


class LabruSpider(scrapy.Spider):
    name = 'labru'
    allowed_domains = ['labirint.ru']
    start_urls = ['https://www.labirint.ru/search/english/?stype=0']

    def parse(self, response: HtmlResponse):

        short_next_page = response.xpath("//a[@class='pagination-next__text']/@href").extract_first()

        if short_next_page:
            next_page = self.start_urls[0][:-8] + short_next_page
            yield response.follow(next_page, callback=self.parse)

        links = [f'https://www.labirint.ru{url.extract()}' for url in response.xpath("//a[@class='cover']/@href")]
        for link in links:
            yield response.follow(link, callback=self.book_parse)

    def book_parse(self, response: HtmlResponse):

        link = response.url
        title = response.xpath("//div[@id='product-title']/h1/text()").extract_first()
        authors = response.xpath("//div[@class='authors']/a/text()").extract()
        price_old = response.xpath("//span[@class='buying-priceold-val-number']/text()").extract_first()
        price_new = response.xpath("//span[@class='buying-pricenew-val-number']/text()").extract_first()
        # price_cur = response.xpath("//span[@class='buying-pricenew-val-currency']/text()").extract_first()
        rate = response.xpath("//div[@id='rate']/text()").extract_first()

        yield BookparserItem(link=link,
                             title=title,
                             authors=authors,
                             price_old=price_old,
                             price_new=price_new,
                             rate=rate)
