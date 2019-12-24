# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy.http import HtmlResponse
from urllib.parse import urlencode


class KrasnodarSpider(scrapy.Spider):

    get_params = {"area": 53, "st": "searchVacancy", "text": "Team lead", "from": "suggest_post", "page": 0}

    query_strings = [
        "Team lead",
        "Python программист"
    ]

    name = 'krasnodar'
    allowed_domains = ['hh.ru']
    start_urls = [
        "https://krasnodar.hh.ru/search/vacancy?{}".format(
            urlencode({
                "area": 53,
                "st": "searchVacancy",
                "text": query_string, "from": "suggest_post"
            })
        ) for query_string in query_strings
    ]

    def parse(self, response: HtmlResponse):
        next_page = response.xpath('//a[contains(@data-qa, "pager-next")]/@href').extract_first()
        if next_page:
            yield from response.follow(next_page, callback=self.parse)

        # Parse page here

        vacancies = [
            link.split("?")[0]
            for link in response.xpath('//a[contains(@data-qa, "vacancy-serp__vacancy-title")]/@href').extract()
        ]
        for vacancy in vacancies:
            yield from response.follow(vacancy, self.parse_vacancy)

    def parse_vacancy(self, response: HtmlResponse):
        """
        Заголовок вакансии
        URL объявления
        Описание вакансии
        Оклад
        Название организации разместившей объявление
        Url на страницу организации на HH

        Далее сохраняем в БД Монго только те вакансии которые имеют указаны размер оклада.
         Если в окладе написано по договоренности или после собеседования и т.д данные не сохраняем.
        @param response:
        @return:
        """
        title = response.xpath('//h1[contains(@data-qa, "vacancy-title")]/span/text()').extract_first()
        salary = response.xpath('//span[contains(@itemprop, "baseSalary")]/span[contains(@itemprop, "value")]/meta[contains(@itemprop, "minValue")]/@content')
        if salary is None:
            salary = response.xpath('//p[contains(@class, "vacancy-salary")]').extract_first()
            salary = re.sub(r"[^\d]+", "", salary) if salary else None
        if not salary or not title:
            yield None

        url = response.url
        description = "".join(response.xpath('//div[@class="vacancy-description"]/*').extract())
        company_section = response.xpath('//a[@class="vacancy-company-name"]/')
        company_url = company_section.xpath("./@href")
        company_name = "".join(company_section.xpath("./*/text()").extract())


