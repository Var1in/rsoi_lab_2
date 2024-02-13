import os
from pathlib import Path

from flask import Flask

from src.config.program_config import ProgramConfiguration
from src.static import routes



class Config(object):
    """
    Класс конфигурации сервера
    """
    JSON_SORT_KEYS = False
    ENV = 'development'
    PRESERVE_CONTEXT_ON_EXCEPTION = False

    def __init__(self, debug_flag):
        self.DEBUG = debug_flag

class ServerConfiguration(object):
    """
    Создание класса конфигурации сервера
    Path('src/config/certificates')

    """
    _instance = None
    __certificates_path = Path(os.getcwd()) / Path('create_certificate')

    def __new__(cls, *args, **kwargs):
        """
        Создание нового объекта конфигурации сервера (singleton)

        :param args:
        :param kwargs:
        """
        if not hasattr(cls, '_instance') or getattr(cls, '_instance') is None:
            cls._instance = super(ServerConfiguration, cls).__new__(cls)
        return cls._instance

    def __init__(self, server_type):
        self._server_type = server_type
        if server_type == 'gunicorn':
            self._app = Flask(__name__)
            ProgramConfiguration()
            return
        self._app = ServerConfiguration.create_flask_app(Config(True if server_type == 'debug' else False))
        self._flask_blueprint = routes
        self._app.register_blueprint(self._flask_blueprint)
        ProgramConfiguration()

    def run(self):
        crt_file_path = self.__certificates_path / 'server.crt'
        key_file_path = self.__certificates_path / 'server.key'
        context = (crt_file_path, key_file_path)
        if self._server_type == 'debug':
            self._app.run('0.0.0.0', port=5000)
        else:
            serve(self._app, host="0.0.0.0", port=5000)

    def unicorn_run(self):
        return self._app

    # def __del__(self):
    #     del self._app
    #     del self._flask_blueprint

    @property
    def app(self):
        return self._app

    @staticmethod
    def create_flask_app(config_class: Config):
        """
        Создание flask приложения

        :param config_class: Конфигурационный класс
        :return: Сущность flask
        """
        flaskApp = Flask(__name__)
        flaskApp.config.from_object(config_class)
        flaskApp.app_context().push()
        return flaskApp
