"""
1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию,
записывающую собранные вакансии в созданную БД.
2. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой больше введённой суммы.
3. Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта.
"""

import requests
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
from pprint import pprint


def split_salary(sal):
    sal = sal.replace(' ', '')
    sal_list = []
    word, num = '', ''
    for char in sal:
        if char.isdigit():
            if word != '':
                sal_list.append(word)
                word = ''
            num += char
        else:
            if num != '':
                sal_list.append(num)
                num = ''
            word += char
    if word != '':
        sal_list.append(word)
    else:
        sal_list.append(num)

    if sal_list[0].isdigit():
        if len(sal_list) > 3:
            min_sal, max_sal, currency = int(sal_list[0]), int(sal_list[2]), sal_list[3]
        else:
            min_sal, max_sal, currency = int(sal_list[0]), int(sal_list[0]), sal_list[1]
    elif sal_list[0] == 'от':
        min_sal, max_sal, currency = int(sal_list[1]), None, sal_list[2]
    else:
        min_sal, max_sal, currency = None, int(sal_list[1]), sal_list[2]

    return min_sal, max_sal, currency


def get_vacs_hh(request_vacancy, max_pages=float('inf')):
    url = 'https://hh.ru'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                             'AppleWebKit/537.36 (KHTML, like Gecko)'
                             'Chrome/92.0.4515.107 Safari/537.36'}
    params = {'text': request_vacancy,
              'items_on_page': '20',
              'clusters': 'true',
              'enable_snippets': 'true',
              'salary': None,
              'st': 'searchVacancy'}
    response = requests.get(url + '/search/vacancy', params=params, headers=headers)

    vacancies_data = []
    cur_page = 0
    while True:
        soup = bs(response.text, 'html.parser')

        vacancies = soup.find_all('div', {'class': 'vacancy-serp-item'})
        for vac in vacancies:
            name_block = vac.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
            name = name_block.getText().replace(u'\xa0', u' ')
            ref_vac = name_block.get('href')
            ref_vac = ref_vac.split('?')[0] if '?' in ref_vac else ref_vac

            employer_block = vac.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
            employer = employer_block.getText().replace(u'\xa0', u' ')
            ref_emp = url + employer_block.get('href')
            ref_emp = ref_emp.split('?')[0] if '?' in ref_emp else ref_emp

            location = vac.find('span', {'data-qa': 'vacancy-serp__vacancy-address'})\
                .getText().replace(u'\xa0', u' ')

            try:
                salary = vac.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})\
                    .getText().replace(u'\u202f', u'')
            except AttributeError:
                salary = None
            if salary:
                min_sal, max_sal, currency = split_salary(salary)
            else:
                min_sal, max_sal, currency = None, None, None

            vac_dict = {'vacancy_name': name, 'vacancy_reference': ref_vac, 'employer': employer,
                        'employer_reference': ref_emp, 'location': location, 'service': 'HeadHunter',
                        'salary': {'min': min_sal, 'max': max_sal, 'currency': currency}}
            vacancies_data.append(vac_dict)

        cur_page += 1
        if cur_page >= max_pages:
            break

        try:
            to_next_page = soup.find('a', {'data-qa': 'pager-next'}).get('href')
            response = requests.get(url + to_next_page, headers=headers)
        except AttributeError:
            break

    return vacancies_data


def get_vacs_sjob(request_vacancy, max_pages=float('inf')):
    url = 'https://russia.superjob.ru'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                             'AppleWebKit/537.36 (KHTML, like Gecko)'
                             'Chrome/92.0.4515.107 Safari/537.36'}
    params = {'keywords': request_vacancy}
    response = requests.get(url + '/vacancy/search/', params=params, headers=headers)

    vacancies_data = []
    cur_page = 0
    while True:
        soup = bs(response.text, 'html.parser')

        vacancies = soup.find_all('div', {'class': 'f-test-vacancy-item'})
        for vac in vacancies:
            name_block = vac.find('a', {'class': 'icMQ_'})
            name = name_block.getText().replace(u'\xa0', u' ')
            ref_vac = url + name_block.get('href')
            ref_vac = ref_vac.split('?')[0] if '?' in ref_vac else ref_vac

            salary = vac.find('span', {'class': '_1h3Zg _2Wp8I _2rfUm _2hCDz _2ZsgW'})\
                .getText().replace(u'\xa0', u'')
            salary = None if salary == 'По договорённости' else salary
            if salary:
                min_sal, max_sal, currency = split_salary(salary)
            else:
                min_sal, max_sal, currency = None, None, None

            try:
                employer_block = next(vac.find('span', {'class': 'f-test-text-vacancy-item-company-name'}).children)
                employer = employer_block.getText().replace(u'\xa0', u' ')
                ref_emp = url + employer_block.get('href')
                ref_emp = ref_emp.split('?')[0] if '?' in ref_emp else ref_emp
            except AttributeError:
                employer = None
                ref_emp = None

            location = list(vac.find('span', {'class': 'f-test-text-company-item-location'}).children)[2] \
                .getText().replace(u'\xa0', u' ')

            vac_dict = {'vacancy_name': name, 'vacancy_reference': ref_vac, 'employer': employer,
                        'employer_reference': ref_emp, 'location': location, 'service': 'SuperJob',
                        'salary': {'min': min_sal, 'max': max_sal, 'currency': currency}}
            vacancies_data.append(vac_dict)

        cur_page += 1
        if cur_page >= max_pages:
            break

        try:
            to_next_page = soup.find('a', {'rel': 'next'}).get('href')
            response = requests.get(url + to_next_page, headers=headers)
        except AttributeError:
            break

    return vacancies_data


def insert_vac_data(request_vacancy, collection, vac_parser, max_pages=float('inf')):
    collection.insert_many(vac_parser(request_vacancy, max_pages))


def update_vacs_hh(request_vacancy, collection):
    url = 'https://hh.ru'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                             'AppleWebKit/537.36 (KHTML, like Gecko)'
                             'Chrome/92.0.4515.107 Safari/537.36'}
    params = {'text': request_vacancy,
              'items_on_page': '20',
              'clusters': 'true',
              'enable_snippets': 'true',
              'salary': None,
              'st': 'searchVacancy'}
    response = requests.get(url + '/search/vacancy', params=params, headers=headers)

    new_vacs = []
    while True:
        soup = bs(response.text, 'html.parser')

        vacancies = soup.find_all('div', {'class': 'vacancy-serp-item'})
        for vac in vacancies:
            name_block = vac.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
            name = name_block.getText().replace(u'\xa0', u' ')
            ref_vac = name_block.get('href')
            ref_vac = ref_vac.split('?')[0] if '?' in ref_vac else ref_vac

            employer_block = vac.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
            employer = employer_block.getText().replace(u'\xa0', u' ')
            ref_emp = url + employer_block.get('href')
            ref_emp = ref_emp.split('?')[0] if '?' in ref_emp else ref_emp

            location = vac.find('span', {'data-qa': 'vacancy-serp__vacancy-address'}) \
                .getText().replace(u'\xa0', u' ')

            try:
                salary = vac.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'}) \
                    .getText().replace(u'\u202f', u'')
            except AttributeError:
                salary = None
            if salary:
                min_sal, max_sal, currency = split_salary(salary)
            else:
                min_sal, max_sal, currency = None, None, None

            vac_dict = {'vacancy_name': name, 'vacancy_reference': ref_vac, 'employer': employer,
                        'employer_reference': ref_emp, 'location': location, 'service': 'HeadHunter',
                        'salary': {'min': min_sal, 'max': max_sal, 'currency': currency}}

            short_ref = ref_vac.split('hh.ru')[1]
            matching = collection.find({'vacancy_reference': {'$regex': short_ref},
                                        'vacancy_name': name})
            if not list(matching):
                collection.insert_one(vac_dict)
                new_vacs.append(vac_dict)

        try:
            to_next_page = soup.find('a', {'data-qa': 'pager-next'}).get('href')
            response = requests.get(url + to_next_page, headers=headers)
        except AttributeError:
            break

    return new_vacs


def update_vacs_sjob(request_vacancy, collection):
    url = 'https://russia.superjob.ru'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                             'AppleWebKit/537.36 (KHTML, like Gecko)'
                             'Chrome/92.0.4515.107 Safari/537.36'}
    params = {'keywords': request_vacancy}
    response = requests.get(url + '/vacancy/search/', params=params, headers=headers)

    new_vacs = []
    while True:
        soup = bs(response.text, 'html.parser')

        vacancies = soup.find_all('div', {'class': 'f-test-vacancy-item'})
        for vac in vacancies:
            name_block = vac.find('a', {'class': 'icMQ_'})
            name = name_block.getText().replace(u'\xa0', u' ')
            ref_vac = url + name_block.get('href')
            ref_vac = ref_vac.split('?')[0] if '?' in ref_vac else ref_vac

            salary = vac.find('span', {'class': '_1h3Zg _2Wp8I _2rfUm _2hCDz _2ZsgW'})\
                .getText().replace(u'\xa0', u'')
            salary = None if salary == 'По договорённости' else salary
            if salary:
                min_sal, max_sal, currency = split_salary(salary)
            else:
                min_sal, max_sal, currency = None, None, None

            try:
                employer_block = next(vac.find('span', {'class': 'f-test-text-vacancy-item-company-name'}).children)
                employer = employer_block.getText().replace(u'\xa0', u' ')
                ref_emp = url + employer_block.get('href')
                ref_emp = ref_emp.split('?')[0] if '?' in ref_emp else ref_emp
            except AttributeError:
                employer = None
                ref_emp = None

            location = list(vac.find('span', {'class': 'f-test-text-company-item-location'}).children)[2] \
                .getText().replace(u'\xa0', u' ')

            vac_dict = {'vacancy_name': name, 'vacancy_reference': ref_vac, 'employer': employer,
                        'employer_reference': ref_emp, 'location': location, 'service': 'SuperJob',
                        'salary': {'min': min_sal, 'max': max_sal, 'currency': currency}}

            short_ref = ref_vac.split('superjob.ru')[1]
            matching = collection.find({'vacancy_reference': {'$regex': short_ref},
                                        'vacancy_name': name})
            if not list(matching):
                collection.insert_one(vac_dict)
                new_vacs.append(vac_dict)

        try:
            to_next_page = soup.find('a', {'rel': 'next'}).get('href')
            response = requests.get(url + to_next_page, headers=headers)
        except AttributeError:
            break

    return new_vacs


def find_salary(salary):
    num = 0
    for collection in [hh, sj]:
        for vac in collection.find({'$or': [{'salary.min': {'$gte': salary},
                                             'salary.currency': 'руб.'},
                                            {'salary.max': {'$gte': salary + 20000},
                                             'salary.min': None,
                                             'salary.currency': 'руб.'}]}):
            num += 1
            pprint([num, vac])


if __name__ == '__main__':
    client = MongoClient('127.0.0.1', 27017)
    db = client['vacancies']
    hh = db.head_hunter
    sj = db.super_job

    request = 'data scientist'
    # request = input('Type a request for considering vacancies:\n')

    # Task #1
    # Filling empty database collections by vacancies:
    insert_vac_data(request, sj, get_vacs_sjob)
    insert_vac_data(request, hh, get_vacs_hh)
    print(f'{hh.count_documents({}) + sj.count_documents({})} vacancies was parsed and added to mongo collections.')

    # Task #2
    # Showing the vacancies with a definite salary:
    find_salary(50000)

    # Task #3
    # Create indexes for reference and name fields:
    hh.create_index([('vacancy_reference', 'text')], name='reference_text_index')
    sj.create_index([('vacancy_reference', 'text')], name='reference_text_index')
    hh.create_index([('vacancy_name', 1)], name='vac_name_index')
    sj.create_index([('vacancy_name', 1)], name='vac_name_index')
    pprint(hh.index_information())
    pprint(sj.index_information())
    # Update the vacancies collections:
    new_hh = update_vacs_hh(request, hh)
    new_sj = update_vacs_sjob(request, sj)
    print(f'{len(new_hh)} new vacancies has been added into hh collection.')
    print(f'{len(new_sj)} new vacancies has been added into sj collection.')
    pprint(new_hh + new_sj)

    # for i in hh.find({'vacancy_reference': {'$regex': '/vacancy/42587352'},
    #                   'vacancy_name': 'Программист Python (Middle)'}):
    #     pprint(i)

    # hh.drop()
    # sj.drop()
    # print(hh.count_documents({}), sj.count_documents({}))
