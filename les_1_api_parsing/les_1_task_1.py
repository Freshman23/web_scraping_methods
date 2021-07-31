""" 1. (Обязательное) Посмотреть документацию к API GitHub, разобраться как вывести список репозиториев
для конкретного пользователя, сохранить JSON-вывод в файле *.json.
"""

import requests
import json

user = 'Freshman23'
url = f'https://api.github.com/users/{user}/repos'
params = {}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/92.0.4515.107 Safari/537.36',
           'Accept': 'application/vnd.github.v3+json'}

response = requests.get(url, headers=headers)
j_data = response.json()

print(f'Repositories of user {j_data[0]["owner"]["login"]}:')
for rep in j_data:
    print(f'* {rep["name"]}')

with open('my_repos.json', 'w', encoding='utf-8') as f:
    json.dump(j_data, f, ensure_ascii=False, indent=4)
