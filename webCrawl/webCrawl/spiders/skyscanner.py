import scrapy
from requests import Request
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import random


class SkyscannerSpider(scrapy.Spider):
    name = 'skyscanner'
    allowed_domains = ['www.skyscanner.com.tw']
    start_urls = ['http://www.skyscanner.com.tw/']

    @staticmethod
    def make_requests_from_url(url):
        return Request(url, dont_filter=True, meta={
            'dont_redirect': True,
            'handle_httpstatus_list': [301, 302, 307, 500]
        })

    def parse(self, response):
        print('searching!!!')
        # url =
        # scrapy.Request(url, callback=self.parse)
        # titles = response.css("div.HeroImage_Content__ZGM1M::text").get()
        # titles = response.css('div.browse-data-route h3::text').getall()
        titles = response.xpath(
            "//*[@class='HeroImage_Content__ZGM1M']/h1/text()").get()

        print(titles)

    # def scrape(self, response):
    #     print('searching!!!')
    #     # titles = response.css("div.HeroImage_Content__ZGM1M::text").get()
    #     # titles = response.css('div.browse-data-route h3::text').getall()
    #     titles = response.xpath(
    #         "//*[@class='HeroImage_Content__ZGM1M']/h1/text()").get()


# 切換 User Agent
class MYUserAgentMiddleware(UserAgentMiddleware):
    def __init__(self, user_agent):
        self.user_agent = user_agent

    def from_crawler(cls, crawler):
        return cls(user_agent=crawler.settings.get('MY_UA_LIST'))

    def process_request(self, request, spider):
        agent = random.choice(self.user_agent)
        request.header['User-Agent'] = agent

# class FakeUserAgentErrorRetryMiddleware(RetryMiddleware):
#
#     def process_exception(self, request, exception, spider):
#         if isinstance(exception, TimeoutError) or isinstance(exception, TCPTimedOutError):
#             return self._retry(request, exception, spider)
