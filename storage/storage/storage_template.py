from pydantic.main import BaseModel

from storage.storage.engine_adaptor import find_template
from storage.storage.storage_interface import Pageable, DataPage


class StorageTemplate(object):

    def __init__(self, table_definition):
        self.template = find_template(table_definition)

    def insert_one(self, one: any, model: BaseModel, name: str) -> BaseModel:
        return self.template.insert_one(one, model, name)

    def insert_all(self, data: list, model: BaseModel, name: str):
        return self.template.insert_all(data, model, name)

    def update_one(self, one: any, model: BaseModel, name: str) -> any:
        return self.template.update_one(one, model, name)

    def update_one_first(self, where: dict, updates: dict, model: BaseModel, name: str) -> BaseModel:
        return self.template.update_one_first(where, updates, model, name)

    def update_(self, where: dict, updates: dict, model: BaseModel, name: str):
        self.template.update_(where, updates, model, name)

    def pull_update(self, where: dict, updates: dict, model: BaseModel, name: str):
        self.template.pull_update(where, updates, model, name)

    def delete_by_id(self, id_: str, name: str):
        self.template.delete_by_id(id_, name)

    def delete_one(self, where: dict, name: str):
        self.template.delete_one(where, name)

    def delete_(self, where: dict, model: BaseModel, name: str):
        self.template.delete_(where, model, name)

    def delete_all(self, model: BaseModel, name: str) -> list:
        raise NotImplementedError("delete_all not implemented")

    def drop_(self, name: str):
        self.template.drop_(name)

    def find_by_id(self, id_: str, model: BaseModel, name: str) -> BaseModel:
        return self.template.find_by_id(id_, model, name)

    def find_one(self, where: dict, model: BaseModel, name: str) -> BaseModel:
        return self.template.find_one(where, model, name)

    def find_(self, where: dict, model: BaseModel, name: str) -> list:
        return self.template.find_(where, model, name)

    def list_all(self, model: BaseModel, name: str) -> list:
        return self.template.list_all(model, name)

    def list_all_select(self, select: dict, model: BaseModel, name: str) -> list:
        pass  # need to do

    def list_(self, where: dict, model: BaseModel, name: str) -> list:
        return self.template.list_(where, model, name)

    def list_select(self, select: dict, where: dict, model: BaseModel, name: str) -> list:
        pass  # need to do

    def page_all(self, sort: list, pageable: Pageable, model: BaseModel, name: str) -> DataPage:
        return self.template.page_all(sort, pageable, model, name)

    def page_(self, where: dict, sort: list, pageable: Pageable, model: BaseModel, name: str) -> DataPage:
        return self.template.page_(where, sort, pageable, model, name)

    def get_topic_factors(self, topic_name):
        return self.template.get_topic_factors(topic_name)

    def check_topic_type(self, topic_name):
        return self.template.check_topic_type(topic_name)

    def get_table_column_default_value(self, table_name, column_name):
        return self.template.get_table_column_default_value(table_name, column_name)

    def clear_metadata(self):
        self.template.clear_metadata()
