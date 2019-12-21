from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from avito import settings
from avito.spiders.avito_rielt import AvitoRieldSpider

if __name__ == '__main__':
    crowler_settings = Settings()
    crowler_settings.setmodule(settings)
    process = CrawlerProcess(crowler_settings)
    process.crawl(AvitoRieldSpider)
    process.start()