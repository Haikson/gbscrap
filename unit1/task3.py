"""
Источник: https://geekbrains.ru/posts

Задача:

необходимо обойти все публикации в блоге и сохранить в MongoDB следующую информацию:
    Заголовок статьи,
    ссылка на статью,
    дата публикации (только дата без времени),
    Имя автора

Обход делаем с помощью BS4 + Requests

"""
import sys, os
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

from datetime import datetime
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath('__file__')), 'task3.log')),
        logging.StreamHandler()
    ])


logger = logging.getLogger()


class GeekBlogParser(object):
    def __init__(self):

        self.base_url = "https://geekbrains.ru"
        self.start_url = "https://geekbrains.ru/posts"
        self.mongo_collection = self.get_mongo_collection()

    @staticmethod
    def get_page_content(url):
        resp = requests.get(url)
        if resp.status_code >= 400:
            return ""
        else:
            return resp.text

    def norm_link(self, url):
        """

        @type url: str
        """
        if url.startswith('/'):
            return self.base_url + url
        return url

    def get_articles_list(self, html_content):
        """

        @param html_content: html content string
        @type html_content: str
        @return:
        """
        soup = BeautifulSoup(html_content, features="lxml")
        links = set()
        for link in soup.findAll('a', {'class': 'post-item__title'}):
            links.add(self.norm_link(link['href']))
        return links

    def get_all_articles_list_pages(self):
        soup = BeautifulSoup(self.get_page_content(self.start_url), features="lxml")
        paginator = soup.find('ul', {'class': 'gb__pagination'})
        pages_count = int(paginator.contents[-2].contents[0].text)
        links = set()
        for i in range(1, pages_count + 1):
            logger.info("Getting articles from page {} of {}".format(i, pages_count))
            url = self.start_url + '?page={}'.format(i)
            links.update(list(self.get_articles_list(self.get_page_content(url))))
        return links

    @staticmethod
    def get_mongo_collection(host='localhost', port=27017):
        mongo_client = MongoClient(host, port)
        db = mongo_client['gb_scrap']
        mongo_collection = db['gb_posts']
        mongo_collection.delete_many({})
        logger.info("Mongodb connected. Collection gb_scrap.gb_posts chosen")
        return mongo_collection

    def add_to_mongo(self, title, url, date, author):
        """
        Заголовок статьи
        ссылка на статью
        дата публикации (только дата без времени)
        Имя автора
        :return:
        """
        self.mongo_collection.insert_one({
            'title': title,
            'url': url,
            'date': date,
            'author': author
        })

    def parse_article(self, url):
        logger.info("Get info for article at: {}".format(url))
        html = self.get_page_content(url)
        soup = BeautifulSoup(html, features="lxml")
        title = soup.find('h1', {'class': 'blogpost-title'}).text
        date = datetime.strptime(
            soup.find('time')['datetime'].split("T")[0],
            "%Y-%m-%d"
        )
        author = soup.find('div', {"itemprop": "author"}).text
        return {
            'title': title,
            'url': url,
            'date': date,
            'author': author
        }


if __name__ == '__main__':

    gb_parser = GeekBlogParser()
    urls_todo = gb_parser.get_all_articles_list_pages()
    for url in urls_todo:
        try:
            gb_parser.add_to_mongo(**gb_parser.parse_article(url))
        except Exception as e:
            print(e)

    collection = gb_parser.mongo_collection
    assert collection.count_documents() == len(urls_todo)
    logger.info("All posts parsed successfully")
