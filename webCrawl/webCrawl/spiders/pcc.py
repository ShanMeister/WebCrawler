import scrapy
from requests import Request
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import pandas as pd
import random
import datetime

SCRAPE_DAY = 7  # Crawl day range
DATA_PER_PAGE = 50  # Data amount of each page
nowDate = datetime.datetime.now()  # Tender end date
pastDate = nowDate - datetime.timedelta(days=SCRAPE_DAY)  # Tender start date


class PccSpider(scrapy.Spider):
    name = 'pcc'
    allowed_domains = ['web.pcc.gov.tw']
    # start_urls = ['http://web.pcc.gov.tw/'] # Home page
    # Skip home page by editing origin url
    start_urls = ['https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic?'
                  'firstSearch=true'
                  '&searchType=basic'
                  '&orgName='
                  '&orgId='
                  '&tenderName='
                  '&tenderId='
                  '&tenderType=TENDER_DECLARATION&tenderWay=TENDER_WAY_ALL_DECLARATION'
                  '&dateType=isNow'
                  '&tenderStartDate=' + str(pastDate.year) + '%2F' + str(pastDate.month) + '%2F' + str(pastDate.day) +
                  '&tenderEndDate=' + str(nowDate.year) + '%2F' + str(nowDate.month) + '%2F' + str(nowDate.day)]

    @staticmethod
    def make_requests_from_url(url):
        return Request(url, dont_filter=True, meta={
            'dont_redirect': True,
            'handle_httpstatus_list': [301, 302, 307, 500]
        })

    def parse(self, response):
        url = 'https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic'

        # df = pd.DataFrame(columns={'titles', 'types', 'deadline', 'budget', 'detail_url'})
        data = dict()   # Create an empty dict to save scraped data

        for i in range(1, DATA_PER_PAGE + 1):
            id_n = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[1]/text()").get()

            org_name = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[2]/text()").get()

            subject = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[3]/a/u/text()").get()

            method = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[5]/text()").get()

            category = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[6]/text()").get()

            declare_date = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[7]/text()").get()

            deadline = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[8]/text()").get()

            budget = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[9]/span/text()").get()

            detail_url = response.xpath(
                "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[10]/div/a/@href").get()

            data.update({'id': id_n.strip(), 'org_name': org_name.strip(), 'subject': subject.strip(), 'method': method.strip(), 'category': category.strip(), 'declare_date': declare_date.strip(), 'deadline': deadline.strip(), 'budget': budget.strip(), 'detail_url': detail_url.strip()})
            print(str(i) + ':' + str(data.values()))

        next_page = response.xpath(
            "//*[@id='pagelinks']/a[1]/@href").get()
        print(next_page)
        next_page_url = str(url) + str(next_page)
        yield scrapy.Request(next_page_url, callback=self.parse)

    # def ScrapeSubPage(self, url):


# 切換 User Agent
class MYUserAgentMiddleware(UserAgentMiddleware):
    def init(self, user_agent):
        self.user_agent = user_agent

    def from_crawler(cls, crawler):
        return cls(user_agent=crawler.settings.get('MY_UA_LIST'))

    def process_request(self, request, spider):
        agent = random.choice(self.user_agent)
        request.header['User-Agent'] = agent
