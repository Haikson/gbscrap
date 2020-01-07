from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from instagram_parser import settings
from instagram_parser.spiders.instagram import InstagramSpider

if __name__ == '__main__':
    crowler_settings = Settings()
    crowler_settings.setmodule(settings)
    process = CrawlerProcess(crowler_settings)
    process.crawl(InstagramSpider)
    process.start()
