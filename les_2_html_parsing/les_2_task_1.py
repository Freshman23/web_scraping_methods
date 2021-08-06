""" Вариант №1.
Необходимо собрать информацию о вакансиях на вводимую должность (используем input или через аргументы
получаем должность) с сайтов HH(обязательно) и/или Superjob(по желанию).
Приложение должно анализировать несколько страниц сайта (также вводим через input или аргументы).
Получившийся список должен содержать в себе минимум:
- Наименование вакансии.
- Предлагаемую зарплату (отдельно минимальную и максимальную).
- Ссылку на саму вакансию.
- Сайт, откуда собрана вакансия.
По желанию можно добавить ещё параметры вакансии (например, работодателя и расположение). Структура должна быть
одинаковая для вакансий с обоих сайтов. Общий результат можно вывести с помощью dataFrame через pandas.
Сохраните в json либо csv.
"""

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd


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

            employer_block = vac.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
            employer = employer_block.getText().replace(u'\xa0', u' ')
            ref_emp = url + employer_block.get('href')

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
                        'min_salary': min_sal, 'max_salary': max_sal, 'vacancy_currency': currency}
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
            except AttributeError:
                employer = None
                ref_emp = None

            location = list(vac.find('span', {'class': 'f-test-text-company-item-location'}).children)[2] \
                .getText().replace(u'\xa0', u' ')

            vac_dict = {'vacancy_name': name, 'vacancy_reference': ref_vac, 'employer': employer,
                        'employer_reference': ref_emp, 'location': location, 'service': 'SuperJob',
                        'min_salary': min_sal, 'max_salary': max_sal, 'vacancy_currency': currency}
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


request = 'data scientist'
# request = input('Type a request for considering vacancies:\n')
df = pd.DataFrame(get_vacs_hh(request) + get_vacs_sjob(request))

file_path = 'data_scientist_response.csv'
df.to_csv(file_path, index=False)

print(f'{df.shape[0]} results of request are saved in file: {file_path}')
print(df[['vacancy_name', 'min_salary']].head(10))
