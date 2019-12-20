# -*- coding: utf-8 -*-
import scrapy


class AvitoSpider(scrapy.Spider):
    name = 'avito'
    allowed_domains = ['avito.ru']
    start_urls = ['https://www.avito.ru/krasnodar/kvartiry/prodam']

    def parse(self, response):
        pass

