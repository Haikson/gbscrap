# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from avito.items import AvitoRieltItem
from datetime import datetime


class AvitoRieldSpider(scrapy.Spider):
    name = 'avito'
    allowed_domains = ['avito.ru']
    start_urls = ['https://www.avito.ru/krasnodar/kvartiry/prodam']
    page_num = 1
    num_pages = None

    def parse(self, response: HtmlResponse):
        if self.num_pages is None:
            self.num_pages = int(response.xpath('//span[contains(@data-marker, "pagination-button/next")]/../span/text()').extract()[-2])
        while self.page_num < self.num_pages:
            self.page_num += 1
            next_page = '?'.join([self.start_urls[0], "p={}".format(self.page_num)])
            apartment_links = response.xpath('//div[contains(@class, "item_table-wrapper")]//a[contains(@class, "snippet-link")]/@href').extract()

            yield response.follow(next_page, callback=self.parse)

            for link in apartment_links:
                yield response.follow(url=link, callback=self.parse_apartment)

    def parse_apartment(self, response: HtmlResponse):
        title = response.xpath('//span[contains(@itemprop, "name")]/text()').extract_first()
        price = response.xpath('//span[contains(@itemprop, "price")]/@content').extract_first()
        params_blocks = response.xpath('//li[contains(@class, "item-params-list-item")]')
        params = [
            {
                'name': param_block.xpath('./span/text()').extract_first(),
                'value': param_block.xpath('./text()').extract_first(),
            } for param_block in params_blocks
        ]
        images = response.xpath('//div[contains(@class, "gallery-img-wrapper")]/div[contains(@class, "gallery-img-frame")]/@data-url').extract()
        item = AvitoRieltItem(
            title=title,
            price=price,
            params=params,
            images=images,
            date_parsed=datetime.now(),
            url=response.url
        )



