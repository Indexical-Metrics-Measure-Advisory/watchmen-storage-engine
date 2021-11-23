from storage.config.config import settings
from storage.model.data_source import DataSource, DataSourceParam

MYSQL = "mysql"
MONGO = "mongo"
ORACLE = "oracle"


def get_default_datasource():
    datasource = DataSource()
    datasource.dataSourceCode = "default"
    datasource.dataSourceType = settings.STORAGE_ENGINE
    if settings.STORAGE_ENGINE == MONGO:
        datasource.username = settings.MONGO_USERNAME
        datasource.password = settings.MONGO_PASSWORD
        datasource.name = settings.MONGO_DATABASE
        datasource.host = settings.MONGO_HOST
        datasource.port = settings.MONGO_PORT
        datasource.dataSourceType = "mongodb"
        return datasource
    elif settings.STORAGE_ENGINE == MYSQL:
        datasource.username = settings.MYSQL_USER
        datasource.password = settings.MYSQL_PASSWORD
        datasource.name = settings.MYSQL_DATABASE
        datasource.host = settings.MYSQL_HOST
        datasource.port = settings.MYSQL_PORT
        datasource.dataSourceType = "mysql"
        return datasource
    elif settings.STORAGE_ENGINE == ORACLE:
        datasource.username = settings.ORACLE_USER
        datasource.password = settings.ORACLE_PASSWORD
        datasource.name = settings.ORACLE_NAME
        datasource.host = settings.ORACLE_HOST
        datasource.port = settings.ORACLE_PORT
        datasource.dataSourceType = "oracle"
        datasource.params = []
        if settings.ORACLE_SERVICE and settings.ORACLE_SERVICE != "":
            ds_param_service = DataSourceParam(**{
                'name': 'service_name',
                'value': settings.ORACLE_SERVICE
            })
            datasource.params.append(ds_param_service)
        if settings.ORACLE_SID and settings.ORACLE_SID != "":
            ds_param_sid = DataSourceParam(**{
                'name': 'SID',
                'value': settings.ORACLE_SID
            })
            datasource.params.append(ds_param_sid)
        return datasource


def find_template(table_definition):
    default_datasource = get_default_datasource()
    if settings.STORAGE_ENGINE == MONGO:
        from storage.mongo.mongo_client import MongoEngine
        from storage.mongo.mongo_template import MongoStorage
        engine = MongoEngine(default_datasource)
        return MongoStorage(engine.get_engine(), table_definition)
    elif settings.STORAGE_ENGINE == MYSQL:
        # from watchmen.database.table.mysql_table_definition import MysqlTableDefinition
        from storage.mysql.mysql_client import MysqlEngine
        from storage.mysql.mysql_template import MysqlStorage
        engine = MysqlEngine(default_datasource)
        return MysqlStorage(engine.get_engine(), table_definition)
    elif settings.STORAGE_ENGINE == ORACLE:
        # from watchmen.database.table import oracle_table_definition
        from storage.oracle.oracle_client import OracleEngine
        from storage.oracle.oracle_template import OracleStorage
        engine = OracleEngine(default_datasource)
        return OracleStorage(engine.get_engine(), table_definition)
