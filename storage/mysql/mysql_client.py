from sqlalchemy import create_engine

from storage.model.data_source import DataSource
from storage.mysql.mysql_engine import dumps


class MysqlEngine(object):

    def __init__(self, datasource: DataSource):
        self.connection_url = 'mysql://%s:%s@%s:%s/%s?charset=utf8' % (datasource.username,
                                                                       datasource.password,
                                                                       datasource.host,
                                                                       datasource.port,
                                                                       datasource.name)
        self.engine = create_engine(self.connection_url,
                                    echo=False,
                                    future=True,
                                    pool_recycle=3600,
                                    json_serializer=dumps, encoding='utf-8')

    def get_engine(self):
        return self.engine
