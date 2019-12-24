# -*- coding: utf-8 -*-
import re
import scrapy
import json
import lxml.html.clean as clean
from scrapy.http import HtmlResponse
from urllib.parse import urlencode

from unit1.hh.hh.items import HhItem


class KrasnodarSpider(scrapy.Spider):

    get_params = {"area": 53, "st": "searchVacancy", "text": "Team lead", "from": "suggest_post", "page": 0}

    query_strings = [
        "Team lead",
        "Python программист"
    ]

    name = 'krasnodar'
    allowed_domains = ['hh.ru']
    base_url = "https://krasnodar.hh.ru"
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
            yield response.follow(next_page, callback=self.parse)

        # Parse page here

        vacancies = [
            link.split("?")[0]
            for link in response.xpath('//a[contains(@data-qa, "vacancy-serp__vacancy-title")]/@href').extract()
        ]
        for vacancy in vacancies:
            yield response.follow(vacancy, callback=self.parse_vacancy)

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
        title = "".join(response.xpath('//h1[contains(@data-qa, "vacancy-title")]//text()').extract())

        salary_data = response.xpath('//script[@data-name="HH/GoogleDfpService"]/@ddata-params').extract_first()
        salary_data = json.loads(salary_data) if salary_data else {
            "vac_type": "standard",
            "vac_views": "607",
            "vac_city": ".113.224.1438.53.",
            "vac_metro": [],
            "vac_employerid": "3941791",
            "vac_salary_from": "350000",
            "vac_salary_to": "650000",
            "vac_salary_cur": "RUR",
            "vac_profarea": ["1"],
            "vac_specs": ["221"],
            "vac_exp": "between3And6",
            "vac_skills": [
            ]
        }

        url = response.url
        description = "".join(
            self.clean_descriptions(response.xpath('//div[@class="vacancy-description"]/*'))
        )
        company_section = response.xpath('//a[@class="vacancy-company-name"]')
        company_url = company_section.xpath("./@href").extract_first()
        company_name = "".join(company_section.xpath("./*/text()").extract())

        yield HhItem(
            title=title,
            salary_from=salary_data.get("vac_salary_from"),
            salary_to=salary_data.get("vac_salary_to"),
            salary_cur=salary_data.get("vac_salary_cur"),
            url=url,
            description=description,
            company_url="".join([self.base_url, company_url]),
            company_name=company_name.strip(),
            skills=salary_data.get("skills", [])
        )

    @staticmethod
    def clean_descriptions(selectors):
        selectors = selectors or []
        safe_attrs = set(['src', 'alt', 'href', 'title', 'width', 'height'])
        kill_tags = ['object', 'iframe']
        cleaner = clean.Cleaner(safe_attrs_only=True, safe_attrs=safe_attrs, kill_tags=kill_tags)

        return [cleaner.clean_html(selector.extract()).strip() for selector in selectors]


