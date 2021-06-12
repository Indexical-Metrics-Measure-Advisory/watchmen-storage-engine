from pymongo import MongoClient

from storage.config.config import settings

client = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT, username=settings.MONGO_USERNAME,
                     password=settings.MONGO_PASSWORD)

db = client[settings.MONGO_SCHEMA]


def get_client():
    return db


def get_client_db():
    return client

#
# def get_monitor_db():
#     return monitor_client[MONITOR]
