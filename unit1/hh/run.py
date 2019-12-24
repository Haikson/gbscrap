from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from hh import settings
from hh.spiders.krasnodar import KrasnodarSpider

if __name__ == '__main__':
    crowler_settings = Settings()
    crowler_settings.setmodule(settings)
    process = CrawlerProcess(crowler_settings)
    process.crawl(KrasnodarSpider)
    process.start()
