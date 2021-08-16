"""
1. Написать программу, которая собирает входящие письма из своего или тестового почтового ящика и
сложить данные о письмах в базу данных (от кого, дата отправки, тема письма, текст письма полный)
Логин тестового ящика: study.ai_172@mail.ru
Пароль тестового ящика: NextPassword172!?

2. Написать программу, которая собирает «Новинки» с сайта техники mvideo и складывает данные в БД.
Сайт можно выбрать и свой. Главный критерий выбора: динамически загружаемые товары.
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

from pymongo import MongoClient
from hashlib import sha1
import getpass
from time import sleep
from datetime import datetime, date, time


def transform_datetime(dt_str):
    dt_map = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
              'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}

    dt_list = dt_str.replace(',', '').replace(':', ' ').split()

    try:
        if len(dt_list) == 4:
            dt = datetime(date.today().year,
                          dt_map[dt_list[1]],
                          int(dt_list[0]),
                          int(dt_list[2]),
                          int(dt_list[3]))
        elif len(dt_list) == 5:
            dt = datetime(int(dt_list[2]),
                          dt_map[dt_list[1]],
                          int(dt_list[0]),
                          int(dt_list[3]),
                          int(dt_list[4]))
        elif len(dt_list) == 3:
            t = time(int(dt_list[1]), int(dt_list[2]))
            dt = datetime.combine(date.today(), t)
        else:
            dt = dt_str
    except KeyError:
        dt = dt_str

    return dt


def get_mail_letters_urls(driver):
    driver.get('https://account.mail.ru/login')

    sleep(2)

    login = driver.find_element_by_name('username')
    req_login = getpass.getpass(prompt='Enter login:')
    login.send_keys(req_login)
    login.send_keys(Keys.ENTER)

    sleep(2)

    password = driver.find_element_by_name('password')
    req_pass = getpass.getpass(prompt='Enter password:')
    password.send_keys(req_pass)
    password.send_keys(Keys.ENTER)

    items = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.CLASS_NAME, 'dataset__items')))
    letters = items.find_elements_by_class_name('js-letter-list-item')
    letters_urls = set()
    for letter in letters:
        letters_urls.add(letter.get_attribute('href'))

    while True:
        actions = ActionChains(driver)
        actions.move_to_element(letters[-1])
        actions.perform()

        outer_break = False

        letters = driver.find_elements_by_class_name('js-letter-list-item')
        for num, letter in enumerate(letters[::-1]):
            url = letter.get_attribute('href')

            if url not in letters_urls:
                letters_urls.add(url)
            else:
                if num == 0:
                    outer_break = True
                break

        if outer_break:
            break

    return list(letters_urls)


def fill_db_by_mail_letters(driver, urls, collection):
    new = 0
    for url in urls:
        driver.get(url)

        title = WebDriverWait(driver, 15).until(ec.presence_of_element_located((By.TAG_NAME, 'h2'))).text
        author = driver.find_element_by_xpath("//*[@class='letter__author']/span").get_attribute('title')
        letter_dt = transform_datetime(driver.find_element_by_class_name('letter__date').text)
        body = driver.find_element_by_xpath("//*[@class='letter__body']").text
        letter_id = sha1((url + title).encode()).hexdigest()

        letter_dict = {'_id': letter_id,
                       'title': title,
                       'author': author,
                       'letter_datetime': letter_dt,
                       'body': body}

        try:
            collection.insert_one(letter_dict)
            new += 1
        except:
            pass

    print('*' * 30)
    print(f'{new} letters has been added into database <mail_letters>')
    print('*' * 30)


def fill_db_by_mvideo_goods(driver, partition, collection):
    driver.get('https://www.mvideo.ru/')

    block = driver.find_element_by_xpath(f"//h2[contains(text(),'{partition}')]/../../..")

    actions = ActionChains(driver)
    actions.move_to_element(block)
    actions.perform()

    next_btn = block.find_element_by_class_name('next-btn')
    while 'disabled' not in next_btn.get_attribute('class').split():
        next_btn.click()

    goods = block.find_elements_by_xpath(".//a[@data-product-info]")[::2]
    goods_list = []
    for good in goods:
        good_str = good.get_attribute('data-product-info').replace('{', '') \
            .replace('}', '')
        good_lst = [pair.strip().replace('"', '').split(': ') for pair in good_str.split('",')]
        good_dict = {k: v for k, v in good_lst}
        goods_list.append(good_dict)

    new = 0

    for good in goods_list:
        good_dict = {'_id': int(good['productId']),
                     'name': good['productName'],
                     'category_name': None,
                     'vendor_name': None,
                     'price': float(good['productPriceLocal'])}
        if good['productCategoryName']:
            good_dict['category_name'] = good['productCategoryName']
        if good['productVendorName']:
            good_dict['vendor_name'] = good['productVendorName']

        try:
            collection.insert_one(good_dict)
            new += 1
        except:
            pass

    print('*' * 30)
    print(f'{new} new goods has been added into database <mvideo>')
    print('*' * 30)


if __name__ == '__main__':
    chrome_options = Options()
    chrome_options.add_argument("start-maximized")
    chrome_driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=chrome_options)

    client = MongoClient('127.0.0.1', 27017)

    # Task 1:
    db_mail = client['mail_letters']
    test_col = db_mail['study.ai_172']
    mail_urls = get_mail_letters_urls(chrome_driver)
    fill_db_by_mail_letters(chrome_driver, mail_urls, test_col)

    # Task 2:
    db_mvideo = client['mvideo']
    new_goods = db_mvideo['new_goods']
    fill_db_by_mvideo_goods(chrome_driver, 'Новинки', new_goods)

    chrome_driver.close()
