import math

from storage.common.data_page import DataPage


def build_data_pages(pagination, result, item_count):
    data_page = DataPage()
    data_page.data = result
    data_page.itemCount = item_count
    data_page.pageSize = pagination.pageSize
    data_page.pageNumber = pagination.pageNumber
    data_page.pageCount = math.ceil(item_count / pagination.pageSize)
    return data_page



def convert_to_dict(instance):
    if type(instance) is not dict:
        return instance.dict(by_alias=True)
    else:
        return instance