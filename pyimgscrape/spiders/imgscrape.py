import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class ImgscrapeSpider(CrawlSpider):
    name = 'imgscrape'

    def __init__(self, url=None, *args, **kwargs):
        self.rules = (
            # This rule set makes sure it downloads anything with the extension .jpg in it and also removes the deny_extensions default setting 
            Rule(LinkExtractor(allow=('.jpg'), deny_extensions=set(), tags = ('img',), attrs=('src',), canonicalize = True, unique = True), follow = False, callback='parse_item'),
        )

        self.start_urls = [url]
        
        super(ImgscrapeSpider, self).__init__(*args, **kwargs)
    

    def parse_item(self, response):
        self.logger.info('------- Begin Parse')
        self.logger.info('Found image - %s', response.url)

        yield {
            'img': f"{response.url}"
        }
    
        
