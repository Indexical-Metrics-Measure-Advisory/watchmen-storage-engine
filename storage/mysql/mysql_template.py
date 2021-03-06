import json
import logging
import operator
from operator import eq

from sqlalchemy import insert, update, and_, or_, delete, desc, asc, \
    text, JSON, inspect,distinct
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from watchmen_boot.cache.cache_manage import cacheman, TOPIC_DICT_BY_NAME
from watchmen_boot.storage.mysql.mysql_utils import parse_obj

from storage.common.data_page import DataPage
from storage.common.utils.storage_utils import build_data_pages
from storage.common.utils.storage_utils import convert_to_dict
from storage.storage.storage_interface import StorageInterface

log = logging.getLogger("app." + __name__)

log.info("mysql template initialized")


# @singleton
class MysqlStorage(StorageInterface):

    def __init__(self, client, table_provider):
        self.engine = client
        self.insp = inspect(client)
        self.table = table_provider

    def build_mysql_where_expression(self, table, where):
        for key, value in where.items():
            if key == "and" or key == "or":
                if isinstance(value, list):
                    result_filters = []
                    for express in value:
                        result = self.build_mysql_where_expression(table, express)
                        result_filters.append(result)
                if key == "and":
                    return and_(*result_filters)
                if key == "or":
                    return or_(*result_filters)
            else:
                if isinstance(value, dict):
                    for k, v in value.items():
                        if k == "=":
                            return table.c[key.lower()] == v
                        if k == "!=":
                            return operator.ne(table.c[key.lower()], v)
                        if k == "like":
                            if v != "" or v != '' or v is not None:
                                return table.c[key.lower()].like("%" + v + "%")
                        if k == "in":
                            if isinstance(table.c[key.lower()].type, JSON):
                                stmt = ""
                                if isinstance(v, list):
                                    # value_ = ",".join(v)
                                    for item in v:
                                        if stmt == "":
                                            stmt = "JSON_CONTAINS(" + key.lower() + ", '[\"" + item + "\"]', '$') = 1"
                                        else:
                                            stmt = stmt + " or JSON_CONTAINS(" + key.lower() + ", '[\"" + item + "\"]', '$') = 1 "
                                else:
                                    value_ = v
                                    stmt = "JSON_CONTAINS(" + key.lower() + ", '[\"" + value_ + "\"]', '$') = 1"
                                return text(stmt)
                            else:
                                if isinstance(v, list):
                                    return table.c[key.lower()].in_(v)
                                elif isinstance(v, str):
                                    v_list = v.split(",")
                                    return table.c[key.lower()].in_(v_list)
                                else:
                                    raise TypeError(
                                        "operator in, the value \"{0}\" is not list or str".format(v))
                        if k == "not-in":
                            if isinstance(table.c[key.lower()].type, JSON):
                                if isinstance(v, list):
                                    value_ = ",".join(v)
                                else:
                                    value_ = v
                                stmt = "JSON_CONTAINS(" + key.lower() + ", '[\"" + value_ + "\"]', '$') = 0"
                                return text(stmt)
                            else:
                                if isinstance(v, list):
                                    return table.c[key.lower()].notin_(v)
                                elif isinstance(v, str):
                                    v_list = ",".join(v)
                                    return table.c[key.lower()].notin_(v_list)
                                else:
                                    raise TypeError(
                                        "operator not_in, the value \"{0}\" is not list or str".format(v))
                        if k == ">":
                            return table.c[key.lower()] > v
                        if k == ">=":
                            return table.c[key.lower()] >= v
                        if k == "<":
                            return table.c[key.lower()] < v
                        if k == "<=":
                            return table.c[key.lower()] <= v
                        if k == "between":
                            if (isinstance(v, tuple)) and len(v) == 2:
                                return table.c[key.lower()].between(v[0],
                                                                    v[1])
                else:
                    return table.c[key.lower()] == value

    @staticmethod
    def build_mysql_order(table, order_: list):
        result = []
        if order_ is None:
            return result
        else:
            for item in order_:
                if isinstance(item, tuple):
                    if item[1] == "desc":
                        new_ = desc(table.c[item[0].lower()])
                        result.append(new_)
                    if item[1] == "asc":
                        new_ = asc(table.c[item[0].lower()])
                        result.append(new_)
            return result

    def insert_one(self, one, model, name):
        table = self.table.get_table_by_name(name)
        one_dict: dict = convert_to_dict(one)
        values = {}
        for key, value in one_dict.items():
            if isinstance(table.c[key.lower()].type, JSON):
                if value is not None:
                    values[key.lower()] = value
                else:
                    values[key.lower()] = None
            else:
                values[key.lower()] = value
        stmt = insert(table).values(values)
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(stmt)
        return model.parse_obj(one)

    def insert_all(self, data, model, name):
        table = self.table.get_table_by_name(name)
        stmt = insert(table)
        value_list = []
        for item in data:
            instance_dict: dict = convert_to_dict(item)
            values = {}
            for key in table.c.keys():
                values[key] = instance_dict.get(key)
            value_list.append(values)
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(stmt, value_list)

    def update_one(self, one, model, name) -> any:
        table = self.table.get_table_by_name(name)
        stmt = update(table)
        one_dict: dict = convert_to_dict(one)
        primary_key = self.table.get_primary_key(name)
        stmt = stmt.where(
            eq(table.c[primary_key.lower()], one_dict.get(primary_key)))
        values = {}
        for key, value in one_dict.items():
            if isinstance(table.c[key.lower()].type, JSON):
                if value is not None:
                    values[key.lower()] = value
                else:
                    values[key.lower()] = None
            else:
                values[key.lower()] = value
        stmt = stmt.values(values)
        with self.engine.connect() as conn:
            with conn.begin():
                result = conn.execute(stmt)
        return model.parse_obj(one)

    def update_one_first(self, where, updates, model, name):
        table = self.table.get_table_by_name(name)
        stmt = update(table)
        stmt = stmt.where(self.build_mysql_where_expression(table, where))
        instance_dict: dict = convert_to_dict(updates)
        values = {}
        for key, value in instance_dict.items():
            if isinstance(table.c[key.lower()].type, JSON):
                if value is not None:
                    values[key.lower()] = value
                else:
                    values[key.lower()] = None
            else:
                values[key.lower()] = value
        stmt = stmt.values(values)
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(stmt)
        return model.parse_obj(updates)

    def update_(self, where, updates, model, name):
        table = self.table.get_table_by_name(name)
        stmt = update(table)
        stmt = stmt.where(self.build_mysql_where_expression(table, where))
        instance_dict: dict = convert_to_dict(updates)
        values = {}
        for key, value in instance_dict.items():
            if key != self.table.get_primary_key(name):
                values[key] = value
        stmt = stmt.values(values)
        session = Session(self.engine, future=True)
        try:
            session.execute(stmt)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def pull_update(self, where, updates, model, name):
        results = self.find_(where, model, name)
        updates_dict = convert_to_dict(updates)
        for key, value in updates_dict.items():
            for res in results:
                if isinstance(getattr(res, key), list):
                    setattr(res, key, getattr(res, key).remove(value["in"][0]))
                    self.update_one(res, model, name)

    def delete_by_id(self, id_, name):
        table = self.table.get_table_by_name(name)
        key = self.table.get_primary_key(name)
        stmt = delete(table).where(eq(table.c[key.lower()], id_))
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(stmt)

    def delete_one(self, where: dict, name: str):
        table = self.table.get_table_by_name(name)
        stmt = delete(table).where(self.build_mysql_where_expression(table, where))
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(stmt)

    def delete_(self, where, model, name):
        table = self.table.get_table_by_name(name)
        if where is None:
            stmt = delete(table)
        else:
            stmt = delete(table).where(self.build_mysql_where_expression(table, where))
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(stmt)

    def find_distinct(self, where: dict, model, name: str, column: str) -> list:
        table = self.table.get_table_by_name(name)
        stmt = select(distinct(table.c[column]))
        where_expression = self.build_mysql_where_expression(table, where)
        if where_expression is not None:
            stmt = stmt.where(where_expression)

        results = []
        with self.engine.connect() as conn:
            for result in list(conn.execute(stmt).fetchall()):
                if result[0]:
                    results.append(result[0])
            return results

    def find_by_id(self, id_, model, name):
        table = self.table.get_table_by_name(name)
        primary_key = self.table.get_primary_key(name)
        stmt = select(table).where(eq(table.c[primary_key.lower()], id_))
        with self.engine.connect() as conn:
            cursor = conn.execute(stmt).cursor
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row is None:
                return None
            else:
                result = {}
                for index, name in enumerate(columns):
                    result[name] = row[index]
                return parse_obj(model, result, table)

    def find_one(self, where, model, name):
        table = self.table.get_table_by_name(name)
        stmt = select(table)
        stmt = stmt.where(self.build_mysql_where_expression(table, where))
        with self.engine.connect() as conn:
            cursor = conn.execute(stmt).cursor
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            result = {}
            if row is None:
                return None
            else:
                for index, name in enumerate(columns):
                    result[name] = row[index]
                return parse_obj(model, result, table)

    def find_(self, where: dict, model, name: str) -> list:
        table = self.table.get_table_by_name(name)
        stmt = select(table)
        where_expression = self.build_mysql_where_expression(table, where)
        if where_expression is not None:
            stmt = stmt.where(where_expression)
        results = []
        with self.engine.connect() as conn:
            cursor = conn.execute(stmt).cursor
            columns = [col[0] for col in cursor.description]
            records = cursor.fetchall()
            if records is None:
                return None
            else:
                for record in records:
                    result = {}
                    for index, name in enumerate(columns):
                        result[name] = record[index]
                    results.append(result)
                return [parse_obj(model, row, table) for row in results]

    def list_all(self, model, name):
        table = self.table.get_table_by_name(name)
        stmt = select(table)
        with self.engine.connect() as conn:
            cursor = conn.execute(stmt).cursor
            columns = [col[0] for col in cursor.description]
            res = cursor.fetchall()
        results = []
        for row in res:
            result = {}
            for index, name in enumerate(columns):
                result[name] = row[index]
            results.append(parse_obj(model, result, table))
        return results

    def list_(self, where, model, name) -> list:
        table = self.table.get_table_by_name(name)
        stmt = select(table).where(self.build_mysql_where_expression(table, where))
        with self.engine.connect() as conn:
            cursor = conn.execute(stmt).cursor
            columns = [col[0] for col in cursor.description]
            res = cursor.fetchall()
        results = []
        for row in res:
            result = {}
            for index, name in enumerate(columns):
                result[name] = row[index]
            results.append(parse_obj(model, result, table))
        return results

    def page_all(self, sort, pageable, model, name) -> DataPage:
        count = self.count_table(name)
        table = self.table.get_table_by_name(name)
        stmt = select(table)
        orders = self.build_mysql_order(table, sort)
        for order in orders:
            stmt = stmt.order_by(order)
        offset = pageable.pageSize * (pageable.pageNumber - 1)
        stmt = stmt.offset(offset).limit(pageable.pageSize)
        results = []
        with self.engine.connect() as conn:
            cursor = conn.execute(stmt).cursor
            columns = [col[0] for col in cursor.description]
            res = cursor.fetchall()
        for row in res:
            result = {}
            for index, name in enumerate(columns):
                result[name] = row[index]
            results.append(parse_obj(model, result, table))
        return build_data_pages(pageable, results, count)

    def page_(self, where, sort, pageable, model, name) -> DataPage:
        count = self.count_table(name)
        table = self.table.get_table_by_name(name)
        stmt = select(table).where(self.build_mysql_where_expression(table, where))
        orders = self.build_mysql_order(table, sort)
        for order in orders:
            stmt = stmt.order_by(order)
        offset = pageable.pageSize * (pageable.pageNumber - 1)
        stmt = stmt.offset(offset).limit(pageable.pageSize)
        results = []
        with self.engine.connect() as conn:
            cursor = conn.execute(stmt).cursor
            columns = [col[0] for col in cursor.description]
            res = cursor.fetchall()
        for row in res:
            result = {}
            for index, name in enumerate(columns):
                result[name] = row[index]
            results.append(parse_obj(model, result, table))
        return build_data_pages(pageable, results, count)

    def clear_metadata(self):
        self.table.metadata.clear()

    def check_topic_type(self, topic_name):
        topic = self._get_topic(topic_name)
        return topic['type']

    def get_topic_factors(self, topic_name):
        topic = self._get_topic(topic_name)
        factors = topic['factors']
        return factors

    def count_table(self, table_name):
        primary_key = self.table.get_primary_key(table_name)
        stmt = 'SELECT count(%s) AS count FROM %s' % (primary_key, table_name)
        with self.engine.connect() as conn:
            cursor = conn.execute(text(stmt)).cursor
            result = cursor.fetchone()
        return result[0]

    def count_topic_data_table(self, table_name):
        stmt = 'SELECT count(%s) AS count FROM %s' % ('id_', table_name)
        with self.engine.connect() as conn:
            cursor = conn.execute(text(stmt)).cursor
            result = cursor.fetchone()
        return result[0]

    def _get_topic(self, topic_name) -> any:
        if cacheman[TOPIC_DICT_BY_NAME].get(topic_name) is not None:
            return cacheman[TOPIC_DICT_BY_NAME].get(topic_name)
        table = self.table.get_table_by_name("topics")
        select_stmt = select(table).where(
            self.build_mysql_where_expression(table, {"name": topic_name}))
        with self.engine.connect() as conn:
            cursor = conn.execute(select_stmt).cursor
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row is None:
                raise
            else:
                result = {}
                for index, name in enumerate(columns):
                    if isinstance(table.c[name.lower()].type, JSON):
                        if row[index] is not None:
                            result[name] = json.loads(row[index])
                        else:
                            result[name] = None
                    else:
                        result[name] = row[index]
                cacheman[TOPIC_DICT_BY_NAME].set(topic_name, result)
                return result
