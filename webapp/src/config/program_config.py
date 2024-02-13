import os
from os import getenv as env
import warnings
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

import requests
from psycopg2 import connect


class ProgramConfiguration(object):
    _instance = None
    __access_token = None
    __headers_token = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    def __new__(cls, *args, **kwargs):
        """
        Создание нового объекта конфигурации сервера (singleton)

        :param args:
        :param kwargs:
        """
        if getattr(cls, '_instance') is None:
            cls._instance = super(ProgramConfiguration, cls).__new__(cls)
            # cls.__access_token = cls.get_authorization_token(cls._instance)
            # cls.__time_get_token = datetime.now()
        return cls._instance

    def __init__(self):
        self.__headers = {
            'Authorization': self.__access_token
        }
        self.__payload = {}

    def update_authorization_token(self):
        if (datetime.now() - self.__time_get_token).seconds / 60 >= 60:
            self.__access_token = self.get_authorization_token()
            self.__headers['Authorization'] = self.__access_token
        return

    def get_authorization_token(self, count_repeat=None):
        response = requests.request("POST", self.__url_token,
                                    headers=self.__headers_token,
                                    data=self.__payload_token)
        access_token = f"Bearer {response.json()['access_token']}"
        if count_repeat is not None and count_repeat > 10:
            raise ConnectionError()
        if response.status_code != 200:
            if count_repeat is None:
                count_repeat = 1
            else:
                count_repeat += 1
            print(response.json())
            access_token = self.get_authorization_token(count_repeat)
        return access_token

    def get_file(self, url_file, count_repeat=None):
        self.update_authorization_token()
        status_code = requests.request("GET", url_file, headers=self.__headers, data=self.__payload).status_code
        file = requests.request("GET", url_file, headers=self.__headers, data=self.__payload).content

        if count_repeat is not None and count_repeat > 10:
            raise ConnectionError(f"Status code {status_code}")

        if status_code != 200:
            if count_repeat is None:
                count_repeat = 1
            else:
                count_repeat += 1
            warnings.warn(f'Try to get file {count_repeat}')
            file, status_code = self.get_file(url_file, count_repeat)

        return file, status_code


class DataBaseSettings:
    _instance = None
    # _database = None
    # _user = None
    # _password = None
    # _host = None
    # _port = None

    def __new__(cls, *args, **kwargs):
        if getattr(cls, "_instance") is None:
            if env('DEBUG_MODE') is None:
                load_dotenv(Path(os.getcwd()) / '.env.dev')
            elif env('DEBUG_MODE') == 1:
                pass
            if env('DB_HOST_R') is not None:
                add_symbol = '_R'
            else:
                add_symbol = ''
            cls._instance = super(DataBaseSettings, cls).__new__(cls)
            cls._database = env('DB_NAME' + add_symbol)
            cls._user = env('DB_USER' + add_symbol)
            cls._password = env('DB_PASSWORD' + add_symbol)
            cls._host = env('DB_HOST' + add_symbol)
            cls._port = env('DB_PORT' + add_symbol)
            cls._initial_schema = 'public'
        return cls._instance

    def __init__(
            self,
            initial_schema=None):
        if initial_schema is None:
            initial_schema = 'public'
        self._connection_row = None
        self._engine_simple = None
        self._engine_hard = None
        self.new_schema = None
        self.create_connection_row()
        return

    def create_connection_row(self):
        if self._connection_row is None:
            self._connection_row = (
                f"postgresql://"
                f"{self._user}:{self._password}"
                f"@{self._host}:{self._port}"
                f"/{self._database}"
            )
        return self._connection_row

    def replace_to_test_connection_row(
            self,
            connection_settings: dict):
        self._user = connection_settings['user']
        self._password = ''
        self._host = connection_settings['host']
        self._port = connection_settings['port']
        self._database = connection_settings['database']
        return

    def cursor_connection_row(self) -> dict:
        return {
            "user": self._user,
            "password": self._password,
            "host": self._host,
            "port": self._port,
            "database": self._database,
        }

    @property
    def engine_hard(self):
        if self._engine_hard is None:
            self._engine_hard = connect(**self.cursor_connection_row())
        return self._engine_hard


    def create_schema(self) -> str:
        schema_name = f'temp_{datetime.now().strftime("%Y%m%d%H%M%S%f")}'
        if self._engine_hard is None:
            self._engine_hard = connect(**self.cursor_connection_row())

        query = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"

        all_tables_template = """
        SELECT t.table_name FROM information_schema.tables t
        WHERE table_schema = '{0}'
        """

        table_names = self.get_data_simple(
            all_tables_template.format(self._initial_schema),
            {}
        )
        table_names = [
            table_name
            for table_name in table_names["table_name"].tolist()
            if not str(table_name).startswith("ref_")
        ]

        copy_template = """
        CREATE TABLE {0}.{2} AS 
        TABLE {1}.{2} with NO DATA;
        """

        with self._engine_hard.cursor() as cursor:
            cursor.execute(query)
            for table_name in table_names:
                copy_table_query = copy_template.format(
                    schema_name,
                    self._initial_schema,
                    table_name
                )
                cursor.execute(copy_table_query)
            self._engine_hard.commit()

        self.new_schema = schema_name
        return schema_name

    def drop_schema(self, schema_name=None) -> bool:
        if schema_name is None:
            schema_name = self.new_schema
        if self._engine_hard is None:
            self._engine_hard = connect(**self.cursor_connection_row())

        query = f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;"

        with self._engine_hard.cursor() as cursor:
            cursor.execute(query)
            self._engine_hard.commit()

        return True

    def __del__(self):
        if getattr(self, '_engine_hard') is not None:
            self._engine_hard.close()
        if getattr(self, '_engine_simple') is not None:
            self._engine_simple.close()
