#!/usr/bin/python
#  -*- coding: utf-8 -*-
""" Queryer for Taiwan government e-procurement website
Modified from the source code provided by https://github.com/ywchiu/pythonetl"""
import scrapy
from webCrawl import settings
from requests import Request
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from webCrawl.items import WebcrawlItem
from dateutil.relativedelta import relativedelta
import random
import datetime
import re
import logging
import psycopg2
from psycopg2.extras import json, DictCursor
import ssl
import logging.config
from errno import errorcode
from smtplib import SMTPException
from email.mime.text import MIMEText
import smtplib

DATA_PER_PAGE = 50  # Data amount of each page
_ERRCODE_DATE = 2
_ERRCODE_FILE = 3

__author__ = "Yu-chun Huang + Suki wang + Daniel Mao"
__version__ = "1.0.0c"


def gen_select_sql(table, start_date, org_names=None, subjects=None, budget=None):
    sql_str = u'SELECT * FROM {} ' \
              u'WHERE (notified <> 1 OR notified IS NULL) ' \
              u'AND (declare_date >= \'{}\') '.format(table, start_date.strftime('%Y-%m-%d'))

    sql_keyword = u''
    if org_names is not None and len(org_names) > 0:
        sql_keyword += u' OR '.join([u'org_name LIKE \'%{}%\''.format(w) for w in org_names])

    if subjects is not None and len(subjects) > 0:
        if sql_keyword:
            sql_keyword += u' OR '
        sql_keyword += u' OR '.join([u'subject LIKE \'%{}%\''.format(w) for w in subjects])

    if sql_keyword:
        sql_str += u' AND (' + sql_keyword + ')'

    if budget is not None and budget > 0:
        sql_str += u' AND (budget >= {} OR budget is null)'.format(budget)

    sql_str += u' ORDER BY budget DESC'
    return sql_str


def gen_update_sql(table, ids=None):
    if ids is None or len(ids) == 0:
        return None
    else:
        sql_str = u'UPDATE {} SET notified = 1 ' \
                  u'WHERE id in ({})'.format(table, ', '.join(['\'' + p + '\'' for p in ids]))
        return sql_str


def send_mail(sender, recipients, subject, message, server, username, pwd):
    # msg = EmailMessage()
    msg = MIMEText(message, 'html', 'utf-8')
    msg["Accept-Charset"] = 'utf-8'
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    # Send the message via our own SMTP server.
    try:
        logging.info('Sending notification Email.')
        s = smtplib.SMTP(server, 25587)
        s.starttls(context=context)
        if username and pwd:
            s.login(username, pwd)
        s.send_message(msg)
        logging.info('Notification Email sent.')
    except SMTPException as e_str:
        logging.error("Error: unable to send email")
        logging.error(e_str)
    except Exception as e:
        logging.error(e)


def run_notify(user, password, host, port, database, m_user, m_password, m_host, config, start):
    if not (user and password and host and port and database):
        logging.error('Database connection information is incomplete.')
        quit()

    connection_info = {'user': user,
                       'password': password,
                       'host': host,
                       'port': port,
                       'database': database
                       }
    if not (m_user and m_host):
        logging.error('Sender email and SMTP host are required.)')
        quit()

    # Log query arguments
    logging.info('Start date: %s', start.strftime('%Y-%m-%d'))

    try:
        f = open(config, encoding='UTF-8')
        config = json.load(f)
    except IOError:
        logging.error('Unable to open notification configuration file.')
        quit(_ERRCODE_FILE)

    # Start query
    try:
        content_template = u'<p><b>[ 項次：{} ]</b><br/>' \
                           u'標案案號：{}<br/>' \
                           u'機關名稱：{}<br/>' \
                           u'標案名稱：{}<br/>' \
                           u'招標方式：{}<br/>' \
                           u'採購性質：{}<br/>' \
                           u'公告日期：{}<br/>' \
                           u'截止投標日期：{}<br/>' \
                           u'預算金額：{}<br/>' \
                           u'標案網址：<a href="{}">{}</a><br/></p>'

        content_footer = u'<br/><p><br/>開發及維護：AI與情資系統科</p>'

        cnx = psycopg2.connect(**connection_info)
        cnx.autocommit = True
        match_ids = set('')

        # receivers
        cursor = cnx.cursor()
        cursor.execute('SELECT email FROM webuser WHERE (subscribe = True)')
        # receivers = []
        # for row in cursor:
        #     receivers.append(row[0])
        receivers = ['danielmao@chtsecurity.com']
        cursor.close()

        for subscriber in config:
            logging.info(subscriber)
            logging.info(receivers)
            org_names = subscriber['keyword_org'] if 'keyword_org' in subscriber else None
            subjects = subscriber['keyword_subject'] if 'keyword_subject' in subscriber else None
            budget = subscriber['budget'] if 'budget' in subscriber else None
            query = gen_select_sql('declaration_notify',
                                   start,
                                   org_names=org_names,
                                   subjects=subjects,
                                   budget=budget)

            cursor = cnx.cursor(cursor_factory=DictCursor)
            cursor.execute(query)

            sn = 1
            content = ''
            for row in cursor:
                budget_str = '' if row['budget'] is None else 'NT$' + '{:20,d}'.format(row['budget']).strip()
                content += content_template.format(sn,
                                                   row['id'],
                                                   row['org_name'],
                                                   row['subject'],
                                                   row['method'],
                                                   row['category'],
                                                   row['declare_date'],
                                                   row['deadline'],
                                                   budget_str,
                                                   row['url'], row['url'])
                match_ids.add(row['id'])
                sn += 1
            cursor.close()
            if not content:
                logging.info('No match is found or all procurements have been notified.')
                continue

            content += content_footer
            content = u'<html><body>' + content + u'</body></html>'
            logging.info(content)

            send_mail(m_user,
                      receivers,
                      '政府採購網公開招標通知 ({})'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
                      content,
                      m_host,
                      m_user,
                      m_password)

        # Mark notified procurements
        if len(match_ids) > 0:
            update_sql = gen_update_sql('declaration_notify', ids=match_ids)
            cursor = cnx.cursor(cursor_factory=DictCursor)
            cursor.execute(update_sql)
            cursor.close()
    except psycopg2.OperationalError as e:
        logging.error(e)
    else:
        cnx.close()


class PccSpider(scrapy.Spider):
    name = 'pcc'
    allowed_domains = ['web.pcc.gov.tw']
    start_urls = ['https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic?' +
                  'firstSearch=true' +
                  '&searchType=basic' +
                  '&orgName=' +
                  '&orgId=' +
                  '&tenderName=' +
                  '&tenderId=' +
                  '&tenderType=TENDER_DECLARATION&tenderWay=TENDER_WAY_ALL_DECLARATION' +
                  '&dateType=isNow']
    #             '&tenderStartDate=' + str(startDate[0]) + '%2F' + str(startDate[1]) + '%2F' + str(startDate[2]) +
    #             '&tenderEndDate=' + str(endDate[0]) + '%2F' + str(endDate[1]) + '%2F' + str(endDate[2])]

    @staticmethod
    def make_requests_from_url(url):
        return Request(url, dont_filter=True, meta={
            'dont_redirect': True,  # Avoid website's anti-bot redirection
            'handle_httpstatus_list': [301, 302, 307, 500]  # Retry when server response these errors
        })

    def parse(self, response):
        url = 'https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic'

        for i in range(1, DATA_PER_PAGE):
            item = WebcrawlItem()
            try:
                id = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[3]/text()").get()

                if id is None:
                    break
                else:
                    id = id.strip()
                    item['id'] = id

                item['org_name'] = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[2]/text()").get().strip()

                subject = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[3]/a/u/span/script/text()").get().strip()
                subject = subject.partition('Geps3.CNS.pageCode2Img("')[2].partition('");')[0]
                item['subject'] = id + " " + subject

                item['method'] = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[5]/text()").get().strip()

                item['category'] = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[6]/text()").get().strip()

                declare_date = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[7]/text()").get().strip()
                date_arr = declare_date.replace('/', '-')
                date_arr = datetime.datetime.strptime('0' + str(date_arr), '%Y-%m-%d')
                date_arr = date_arr + relativedelta(years=1911)
                item['declare_date'] = date_arr.date()

                deadline = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[8]/text()").get().strip()
                deadline = deadline.replace('/', '-')
                deadline = datetime.datetime.strptime('0' + str(deadline), '%Y-%m-%d')
                deadline = deadline + relativedelta(years=1911)
                item['deadline'] = deadline.date()

                budget = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[9]/span/text()").get().strip()
                item['budget'] = re.sub('[,]', '', budget)

                url = response.xpath(
                    "//*[@id='tpam']/tbody/tr[" + str(i) + "]/td[10]/div/a/@href").get().strip()
                item['url'] = 'https://web.pcc.gov.tw' + str(url)

                yield item
            except Exception as ex:
                self.logger.warning(ex)

        next_page = response.xpath(
            "//*[@id='pagelinks']/a[1]/@href").get()
        if next_page is not None:
            self.logger.info('Next page...')
            next_page_url = str(url) + str(next_page)
            yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.logger.info('No more data, stop crawling...')
            # send mail
            user = settings.MYSQL_USERNAME
            password = settings.MYSQL_PASSWORD
            host = settings.MYSQL_HOST
            port = settings.MYSQL_PORT
            database = settings.MYSQL_DATABASE
            # SMTP arguments
            m_user = settings.MAIL_USER
            m_password = settings.MAIL_PASSWORD
            m_host = settings.MAIL_HOST
            config = settings.CONFIG
            # errorfile
            err_filename = 'error'
            start = datetime.date.today()

            run_notify(user, password, host, port, database, m_user, m_password, m_host, config, start)

# Switch User Agent
class MYUserAgentMiddleware(UserAgentMiddleware):
    def init(self, user_agent):
        self.user_agent = user_agent

    def from_crawler(cls, crawler):
        return cls(user_agent=crawler.settings.get('MY_UA_LIST'))

    def process_request(self, request, spider):
        agent = random.choice(self.user_agent)
        request.header['User-Agent'] = agent
