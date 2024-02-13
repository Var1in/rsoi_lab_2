import json
import os
import unittest
from io import StringIO
from os import getenv as env
import requests

# import psycopg2
# import testing.postgresql
from pathlib import Path
from dotenv import load_dotenv

base_path = '/api/v1/'

def modify_env(params: dict):
    config = StringIO(
        f"DB_NAME={params['database']}\n"
        f"DB_USER={params['user']}\n"
        f"DB_PORT={params['port']}\n"
        f"DB_PASSWORD=\n"
        f"DB_HOST={params['host']}\n"
        f"DEBUG_MODE=1"
        )
    load_dotenv(stream=config)


class StatusAppTests(unittest.TestCase):
    status_mapping = base_path + 'check_status'
    res_service_port = env('RESERVE_PORT')
    pay_service_port = env('PAYMENT_PORT')
    loy_service_port = env('LOYALTY_PORT')

    @classmethod
    def setUpClass(cls) -> None:
        pass

    def setUp(self) -> None:
        # path = Path(os.getcwd()).parent
        from src import ProgramConfiguration, routes, ServerConfiguration
        self.app = ServerConfiguration('gunicorn').app
        # self.app.config['TESTING'] = True
        self.app.register_blueprint(routes)
        self.app = self.app.test_client()

        self.app_config = ProgramConfiguration()

    def test_run_status(self):
        res = self.app.get(self.status_mapping)
        self.assertEqual(200, res.status_code, f'This mapping is not working: "{self.status_mapping}"')

    def test_services_running(self):
        services_info = [
            ('gateway', ':8080'),
            ('reserve_service', self.res_service_port),
            ('payment_service', self.pay_service_port),
            ('loyalty_service', self.loy_service_port)
        ]
        for body, port in services_info:
            try:
                res = requests.get('http://' + body + str(port) + '/manage/health')
            except ConnectionError:
                self.assertEqual(200, 500, f'Service {body} returned False')

    def test_get_hotel_working(self):
        api_map = 'hotels'
        res = self.app.get(base_path + api_map)
        self.assertEqual(200, res.status_code, f'This mapping is not working: "{base_path + api_map}"')
        return

    def test_get_user_info(self):
        api_map = 'me'
        res = requests.get('http://gateway:8080' + base_path + api_map, headers={'X-User-Name': 'Test Max'})
        # res = self.app.get(base_path + api_map)
        self.assertEqual(200, res.status_code, f'This mapping is not working: "{base_path + api_map}"')

    def test_get_loy_info(self):
        api_map = 'api/loyalty/user_info'
        http_map = f'http://loyalty_service{self.loy_service_port}/{api_map}/Test Max'
        res = requests.get(http_map)
        self.assertEqual(200, res.status_code, f'This mapping is not working: "{http_map}"')

    def test_get_reservations_info(self):
        api_map = 'reservations'
        res = requests.get(f'http://gateway:8080{base_path}{api_map}', headers={'X-User-Name': 'Test Max'})
        self.assertEqual(200, res.status_code, f'This mapping is not working: "{base_path + api_map}"')

    @classmethod
    def tearDownClass(cls) -> None:
        pass


if __name__ == '__main__':
    unittest.main()
