import scrapy
from scrapy.http import HtmlResponse
import re
import json
from instaparser.items import InstaparserItem


class InstacomSpider(scrapy.Spider):
    name = 'instacom'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com']
    insta_auth_link = 'https://www.instagram.com/accounts/login/ajax/'
    insta_login = input('Enter login for an authorization:')
    insta_enc_pass = input('Enter encrypted password for an authorization:')
    users = [user.strip() for user in input('Enter usernames separated by a commas:').split(',')]
    api_url = 'https://i.instagram.com/api/v1/friendships/'

    def parse(self, response: HtmlResponse, **kwargs):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(self.insta_auth_link,
                                 method='POST',
                                 callback=self.authentification,
                                 formdata={'username': self.insta_login,
                                           'enc_password': self.insta_enc_pass},
                                 headers={'X-CSRFToken': csrf})

    def authentification(self, response: HtmlResponse):
        j_body = response.json()
        if j_body['authenticated']:
            for user in self.users:
                yield response.follow(f'/{user}/',
                                      callback=self.user_data_parse,
                                      cb_kwargs={'username': user})

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        url_following = f'{self.api_url}{user_id}/following/?count=12'
        url_followers = f'{self.api_url}{user_id}/followers/?count=12'

        yield response.follow(url_following,
                              callback=self.follow_parse,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'fol_list': 'following'},
                              headers={'User-Agent': 'Instagram 155.0.0.37.107'})
        yield response.follow(url_followers,
                              callback=self.follow_parse,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'fol_list': 'followers'},
                              headers={'User-Agent': 'Instagram 155.0.0.37.107'})

    def follow_parse(self, response: HtmlResponse, username, user_id, fol_list):
        j_data = response.json()
        if j_data.get('next_max_id'):
            max_id = j_data.get('next_max_id')

            if fol_list == 'following':
                url_following = f'{self.api_url}{user_id}/following/?count=12&max_id={max_id}'
                yield response.follow(url_following,
                                      callback=self.follow_parse,
                                      cb_kwargs={'username': username,
                                                 'user_id': user_id,
                                                 'fol_list': fol_list},
                                      headers={'User-Agent': 'Instagram 155.0.0.37.107'})

            elif fol_list == 'followers':
                url_followers = f'{self.api_url}{user_id}/followers/?count=12&max_id={max_id}'
                yield response.follow(url_followers,
                                      callback=self.follow_parse,
                                      cb_kwargs={'username': username,
                                                 'user_id': user_id,
                                                 'fol_list': fol_list},
                                      headers={'User-Agent': 'Instagram 155.0.0.37.107'})

        fol_users = j_data.get('users')
        for user in fol_users:
            yield InstaparserItem(follow_list=fol_list,
                                  fol_username=user.get('username'),
                                  fol_user_id=user.get('pk'),
                                  pic_url=user.get('profile_pic_url'),
                                  j_body=user,
                                  username=username,
                                  user_id=user_id
                                  )

    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        matched = re.search('{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text).group()
        return json.loads(matched).get('id')
