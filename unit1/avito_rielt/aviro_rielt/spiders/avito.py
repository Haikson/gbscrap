# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse


class AvitoSpider(scrapy.Spider):
    name = 'avito'
    allowed_domains = ['avito.ru']
    start_urls = ['https://www.avito.ru/krasnodar/kvartiry/prodam']
    page_num = 1
    num_pages = None

    def parse(self, response: HtmlResponse):
        if self.num_pages is None:
            self.num_pages = int(response.xpath('//span[contains(@data-marker, "pagination-button/next")]/..').extract_first())
        while self.page_num < self.num_pages:
            next_page = '?'.join([self.start_urls[0], "p={}".format(self.page_num)])
            apartment_links = response.xpath('//div[contains(@class, "item_table-wrapper")]//a[contains(@class, "snippet-link")]/@href').extract()

            yield response.follow(next_page, callback=self.parse)


            pass

        pass

