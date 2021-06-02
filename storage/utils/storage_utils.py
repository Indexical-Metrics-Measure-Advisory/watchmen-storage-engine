import math

from pydantic.tools import lru_cache

from storage.common.data_page import DataPage


@lru_cache(maxsize=50)
def build_collection_name(topic_name):
    return "topic_" + topic_name


def build_data_pages(pagination, result, item_count):
    data_page = DataPage()
    data_page.data = result
    data_page.itemCount = item_count
    data_page.pageSize = pagination.pageSize
    data_page.pageNumber = pagination.pageNumber
    data_page.pageCount = math.ceil(item_count / pagination.pageSize)
    return data_page


def check_fake_id(id: str) -> bool:
    return id.startswith('f-', 0, 2)


def convert_to_dict(instance):
    if type(instance) is not dict:
        return instance.dict(by_alias=True)
    else:
        return instance
