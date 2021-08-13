"""
1. Написать приложение, которое собирает основные новости с сайта на выбор news.mail.ru, lenta.ru, yandex-новости.
Для парсинга использовать XPath. Структура данных должна содержать:
- название источника;
- наименование новости;
- ссылку на новость;
- дата публикации.
2. Сложить собранные данные в БД.
Минимум один сайт, максимум - все три
"""

import requests
from lxml import html
from pymongo import MongoClient
from pprint import pprint
from datetime import date
from hashlib import sha1


def get_news_mail(collection):
    url = 'https://news.mail.ru/'
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                            'AppleWebKit/537.36 (KHTML, like Gecko)'
                            'Chrome/92.0.4515.131 Safari/537.36'}
    response = requests.get(url, headers=header)
    dom = html.fromstring(response.text)

    link_list = dom.xpath("//td[@class='daynews__main']//a/@href | "
                          "//td[@class='daynews__items']//a/@href | "
                          "//ul[contains(@class,'list_half')]/li[@class='list__item']//@href")
    news_list = []
    new = 0
    for link in link_list:
        response = requests.get(link, headers=header)
        article = html.fromstring(response.text)

        link_id = link.split('/')[-2]

        title = article.xpath(f"//div[@data-news-id={link_id}]//h1/text()")[0]
        source = article.xpath(f"//div[@data-news-id={link_id}]//a[@class]//text()")[0]
        publication_datetime = article.xpath(f"//div[@data-news-id={link_id}]//@datetime")[0]\
            .replace('T', ' ')[:16]

        news_dict = {'news_title': title, 'news_link': link, 'source': source,
                     'publication_datetime': publication_datetime}
        news_dict['_id'] = sha1((news_dict['news_link'] + news_dict['news_title']).encode()).hexdigest()

        news_list.append(news_dict)

        try:
            collection.insert_one(news_dict)
            new += 1
        except:
            pass

    print('*' * 30)
    print(f'{new} news has been added into <news.mail>')
    print('*' * 30)

    return news_list


def get_news_yandex(collection):
    url = 'https://yandex.ru/news/'
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                            'AppleWebKit/537.36 (KHTML, like Gecko)'
                            'Chrome/92.0.4515.131 Safari/537.36'}
    response = requests.get(url, headers=header)
    dom = html.fromstring(response.text)

    articles = dom.xpath("//div[contains(@class,'news-top-flexible-stories')]//article")
    news_list = []
    new = 0
    for article in articles:
        title = article.xpath(".//h2/text()")[0].replace('\xa0', ' ')
        link = article.xpath(".//a[@class='mg-card__link']/@href")[0]
        source = article.xpath(".//a[@class='mg-card__source-link']/text()")[0]
        publication_time = article.xpath(".//span[@class='mg-card-source__time']/text()")[0]

        news_dict = {'news_title': title, 'news_link': link, 'source': source,
                     'publication_datetime': f'{str(date.today())} {publication_time}'}
        news_dict['_id'] = sha1((news_dict['news_link'] + news_dict['news_title']).encode()).hexdigest()

        news_list.append(news_dict)

        try:
            collection.insert_one(news_dict)
            new += 1
        except:
            pass

    print('*' * 30)
    print(f'{new} news has been added into <news.yandex>')
    print('*' * 30)

    return news_list


def get_news_lenta(collection):
    url = 'https://lenta.ru'
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                            'AppleWebKit/537.36 (KHTML, like Gecko)'
                            'Chrome/92.0.4515.131 Safari/537.36'}
    response = requests.get(url, headers=header)
    dom = html.fromstring(response.text)

    articles = dom.xpath("//section[contains(@class,'b-top7-for-main')]//div[@class='first-item']/h2/a | "
                         "//section[contains(@class,'b-top7-for-main')]//div[@class='item']/a")
    news_list = []
    new = 0
    for article in articles:
        title = article.xpath("./text()")[0].replace('\xa0', ' ')
        link = url + article.xpath("./@href")[0]
        source = 'lenta.ru'
        dt_list = article.xpath(".//@datetime")[0].split()
        dt_map = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05', 'июня': '06',
                  'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'}
        publication_datetime = f'{dt_list[3]}-{dt_map[dt_list[2]]}-{dt_list[1]} ' \
                               f'{dt_list[0][:-1]}'

        news_dict = {'news_title': title, 'news_link': link, 'source': source,
                     'publication_datetime': publication_datetime}
        news_dict['_id'] = sha1((news_dict['news_link'] + news_dict['news_title']).encode()).hexdigest()

        news_list.append(news_dict)

        try:
            collection.insert_one(news_dict)
            new += 1
        except:
            pass

    print('*' * 30)
    print(f'{new} news has been added into <news.lenta>')
    print('*' * 30)

    return news_list


if __name__ == '__main__':
    client = MongoClient('127.0.0.1', 27017)
    db = client['news']
    mail = db.mail
    yandex = db.yandex
    lenta = db.lenta

    pprint(get_news_mail(mail) + get_news_yandex(yandex) + get_news_lenta(lenta))
