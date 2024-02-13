base_path = '/api/v1'

reserve_service_path = '/api/reserve'
payment_service_path = '/api/payment'
loyalty_service_path = '/api/loyalty'

from src.static.api_routes.check_work import *
# from src.static.api_routes.work_with_person import *
from src.static.api_routes.gateway import *
from src.static.api_routes.reserve_service import *
from src.static.api_routes.loyalty_service import *
from src.static.api_routes.payment_service import *
