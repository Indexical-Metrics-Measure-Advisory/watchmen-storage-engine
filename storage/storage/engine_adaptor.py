from storage.config.config import settings

MYSQL = "mysql"
MONGO = "mongo"
ORACLE = "oracle"


def find_template():
    # print(settings.STORAGE_ENGINE)
    if settings.STORAGE_ENGINE == MONGO:
        from storage.mongo import mongo_new_template
        return mongo_new_template
    elif settings.STORAGE_ENGINE == MYSQL:
        from storage.mysql import mysql_template
        return mysql_template
    elif settings.STORAGE_ENGINE == ORACLE:
        from storage.oracle import oracle_template
        return oracle_template
