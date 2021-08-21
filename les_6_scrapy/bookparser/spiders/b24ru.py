import scrapy
from scrapy.http import HtmlResponse
from bookparser.items import BookparserItem


class B24ruSpider(scrapy.Spider):
    name = 'b24ru'
    allowed_domains = ['book24.ru']
    start_urls = ['https://book24.ru/search/?q=english']
    page = 1

    def parse(self, response: HtmlResponse):
        if response.status != 404:
            self.page += 1
            next_page = f'https://book24.ru/search/page-{self.page}/?q=english'
            yield response.follow(next_page, callback=self.parse)

            links = [f'https://book24.ru{url.extract()}'for url in response.xpath(
                "//div[@class='catalog__product-list-holder']//a[contains(@class,'product-card__image')]/@href")]
            for link in links:
                yield response.follow(link, callback=self.book_parse)

    def book_parse(self, response: HtmlResponse):
        link = response.url
        title = response.xpath("//h1[@itemprop='name']/text()").extract_first()
        authors = response.xpath("//div[@id='product-characteristic']//a[contains(@href,'/author/')]/@title").extract()
        price_old = response.xpath("//span[@class='app-price product-sidebar-price__price-old']/text()").extract_first()
        price_new = response.xpath("//span[@class='app-price product-sidebar-price__price']/text()").extract_first()
        # price_cur = response.xpath("//span[@class='buying-pricenew-val-currency']/text()").extract_first()
        rate = response.xpath("//span[@class='rating-widget__main-text']/text()").extract_first()

        yield BookparserItem(link=link,
                             title=title,
                             authors=authors,
                             price_old=price_old,
                             price_new=price_new,
                             rate=rate)
