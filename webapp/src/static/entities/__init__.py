from src.config.program_config import DataBaseSettings
from peewee import *


class BaseModel(Model):
    class Meta:
        database = PostgresqlDatabase(**DataBaseSettings().cursor_connection_row())