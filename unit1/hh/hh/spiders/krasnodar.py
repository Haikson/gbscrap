# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from urllib.parse import urlencode


class KrasnodarSpider(scrapy.Spider):
    name = 'krasnodar'
    allowed_domains = ['hh.ru']
    start_urls = ['https://krasnodar.hh.ru/']
    search_template = "https://krasnodar.hh.ru/search/vacancy?{}"
    get_params = {"area": 53, "st": "searchVacancy", "text": "Team+lead", "from": "suggest_post", "page": 0}
    num_page = 0

    query_strings = [
        "Team lead",
        "Python программист"
    ]

    def parse(self, response: HtmlResponse):
        for query_string in self.query_strings:
            self.get_params.update({"text": query_string})
            next_page = self.search_template.format(urlencode(self.get_params))
            yield response.follow(next_page, callback=self.parse)

            # Parse page here

