# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from webCrawl import settings
from datetime import datetime, date
import logging
import psycopg2


trantab = str.maketrans(
        {'\'': '\\\'',
         '\"': '\\\"',
         '\b': '\\b',
         '\n': '\\n',
         '\r': '\\r',
         '\t': '\\t',
         '\\': '\\\\', })


def gen_insert_sql(table, data_dict):
    # sql_template = u'INSERT INTO {} ({}) VALUES ({}) ON DUPLICATE KEY UPDATE {}'
    sql_template = u'INSERT INTO {} ({}) VALUES ({}) ON CONFLICT (id) DO  UPDATE SET {}'
    columns = ''
    values = ''
    dup_update = ''

    for k, v in data_dict.items():
        if v is not None:
            if values != '':
                columns += ','
                values += ','
                dup_update += ','

            columns += k

            if isinstance(v, str):
                vstr = '\'' + v.translate(trantab) + '\''
            elif isinstance(v, bool):
                vstr = '1' if v else '0'
            elif isinstance(v, datetime) or isinstance(v, date):
                vstr = '\'' + str(v) + '\''
            else:
                vstr = str(v)

            values += vstr
            dup_update += k + '=' + vstr

    sql_str = sql_template.format(table, columns, values, dup_update)
    return sql_str


class WebcrawlPipeline:
    @staticmethod
    def process_item(item, spider):
        print("gen_result: "+gen_insert_sql('declaration_notify', item))
        db_settings = {
            'host': settings.MYSQL_HOST,
            'database': settings.MYSQL_DATABASE,
            'user': settings.MYSQL_USERNAME,
            'password': settings.MYSQL_PASSWORD,
            'port': settings.MYSQL_PORT
        }

        try:
            cnx = psycopg2.connect(**db_settings)
            cnx.autocommit()
            cur = cnx.cursor()
            try:
                cur.execute(gen_insert_sql('declaration_notify', item))
                try:
                    sql = 'SELECT * FROM declaration_notify ORDER BY declare_date DESC FETCH NEXT 1 ROWS ONLY'
                    result = cur.execute(sql)
                    logging.info('SELECT INFO: ' + str(result))
                except Exception as ex:
                    logging.warning(ex)
            except Exception as ex:
                logging.warning('Connect to SQL fail... %s', ex)
            cnx.commit()
            cur.close()
            cnx.close()
        except Exception as ex:
            logging.warning("Exception: %s", ex)
        return item

