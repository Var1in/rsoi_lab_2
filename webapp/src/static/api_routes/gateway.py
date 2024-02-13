import json
from datetime import datetime
from os import getenv as env

import requests
from dateutil.relativedelta import relativedelta
from flask import make_response, request

from src.static import routes
from . import base_path, reserve_service_path, loyalty_service_path, payment_service_path

flask_blueprint = routes

# mapping = base_path + '/hotels'

res_service_port = env('RESERVE_PORT')
if res_service_port is None:
    res_service_port = ''

pay_service_port = env('PAYMENT_PORT')
if pay_service_port is None:
    pay_service_port = ''

loy_service_port = env('LOYALTY_PORT')
if loy_service_port is None:
    loy_service_port = ''

reserve_service = env('RESERVATION_SERVICE')
if reserve_service is None:
    reserve_service = 'http://reserve_service'

loyalty_service = env('LOYALTY_SERVICE')
if loyalty_service is None:
    loyalty_service = 'http://loyalty_service'

payment_service = env('PAYMENT_SERVICE')
if payment_service is None:
    payment_service = 'http://payment_service'


@flask_blueprint.route(base_path + '/hotels', methods=['GET'])
def get_hotels_from_service():
    params = request.args
    page = int(params.get('page', 1))
    size = int(params.get('size', 1))

    if len(request.data) == 0:
        request_json = request.form.to_dict()
    else:
        request_json = json.loads(request.data)

    result = requests.get(
        f'{reserve_service}{res_service_port}{reserve_service_path}/hotels',
        params={'page': page, 'size': size}
    )

    if result.status_code != 200:
        return make_response(
            'Smth is incorrect',
            result.status_code
        )

    return make_response(
        result.json(),
        200
    )


@flask_blueprint.route(base_path + '/me', methods=['GET'])
def get_info_about_user():
    user_uuid = request.headers.get('X-User-Name')
    if user_uuid is None or len(user_uuid) == 0:
        return make_response(
            {'message': 'Empty header X-User-Name'},
            400
        )

    result_reservations = requests.get(
        f'{reserve_service}{res_service_port}{reserve_service_path}/user_info/{user_uuid}'
    )

    if result_reservations.status_code != 200:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_reservations.status_code
        )

    result_reservations = result_reservations.json()

    result_loyalty = requests.get(
        f'{loyalty_service}{loy_service_port}{loyalty_service_path}/user_info/{user_uuid}'
    )

    if result_loyalty.status_code != 200:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_loyalty.status_code
        )

    for reservation in result_reservations:
        result_payment = requests.get(
            f'{payment_service}{pay_service_port}{payment_service_path}/payment/{reservation["payment_uid"]}'
        )

        if result_payment.status_code != 200:
            return make_response(
                {'message': 'Smth is incorrect'},
                result_payment.status_code
            )
        result_payment = result_payment.json()
        reservation['payment'] = result_payment
        del reservation['payment_uid']

    total_result = {
        'reservations': result_reservations,
        'loyalty': result_loyalty.json()
    }

    return make_response(
        total_result,
        200
    )


@flask_blueprint.route(base_path + '/reservations', methods=['GET'])
def get_info_about_reservations():
    user_uuid = request.headers.get('X-User-Name')
    if user_uuid is None or len(user_uuid) == 0:
        return make_response(
            {'message': 'Empty header X-User-Name'},
            400
        )

    result_reservations = requests.get(
        f'{reserve_service}{res_service_port}{reserve_service_path}/user_info/{user_uuid}'
    )

    if result_reservations.status_code != 200:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_reservations.status_code
        )

    result_reservations = result_reservations.json()

    for reservation in result_reservations:

        result_payment = requests.get(
            f'{payment_service}{pay_service_port}{payment_service_path}/payment/{reservation["payment_uid"]}'
        )

        if result_payment.status_code != 200:
            return make_response(
                {'message': 'Smth is incorrect'},
                result_payment.status_code
            )
        result_payment = result_payment.json()

        reservation['payment'] = result_payment
        del reservation['payment_uid']


    # result_reservations['']
    return make_response(
        result_reservations,
        200
    )


@flask_blueprint.route(base_path + '/reservations', methods=['POST'])
def reserve_hotel():
    user_uuid = request.headers.get('X-User-Name')
    if user_uuid is None or len(user_uuid) == 0:
        return make_response(
            {'message': 'Empty header X-User-Name'},
            400
        )

    required_fields = {
        'hotelUid': str,
        'startDate': datetime.fromisoformat,
        'endDate': datetime.fromisoformat
    }

    if len(request.data) == 0 and len(request.form) == 0:
        return make_response({
            'message': 'Invalid data',
            'errors': {
                field: 'string' if f_type is str else 'integer' for field, f_type in required_fields.items()
            },
            'entered_data': request.data.decode()
        }, 400)

    if len(request.data) == 0:
        request_json = request.form.to_dict()
    else:
        request_json = json.loads(request.data)

    errors = {}
    for field, f_type in required_fields.items():

        if (value := request_json.get(field)) is None:
            errors[field] = 'string' if f_type is str else 'datetime'
            continue

        try:
            request_json[field] = f_type(value)
        except ValueError:
            errors[field] = 'string' if f_type is str else 'datetime'

    if len(errors.keys()) > 0:
        return make_response({
            'message': 'Invalid data',
            'errors': {
                field: 'string' if f_type is str else 'integer' for field, f_type in errors.items()
            }
        }, 400)

    # Конец проверки данных

    result_loyalty = requests.get(
        f'{loyalty_service}{loy_service_port}{loyalty_service_path}/user_info/{user_uuid}'
    )

    if result_loyalty.status_code != 200:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_loyalty.status_code
        )

    result_loyalty = result_loyalty.json()

    hotel_price = requests.get(
        f'{reserve_service}{res_service_port}{reserve_service_path}/hotel_price/{request_json["hotelUid"]}'
    )

    if hotel_price.status_code != 200:
        return make_response(
            {'message': 'Reserve service returned'},
            result_loyalty.status_code
        )

    hotel_price = hotel_price.json()['price']
    loyalty_discount = result_loyalty['discount']
    days = relativedelta(request_json['endDate'], request_json['startDate']).days

    total_price = hotel_price * days * (1 - loyalty_discount / 100)

    result_pay = requests.post(
        f'{payment_service}:{pay_service_port}{payment_service_path}/set_pay',
        data={
            'price': int(total_price)
        }
    )

    if result_pay.status_code != 201:
        return make_response(
            {'message': 'Payment service returned'},
            result_pay.status_code
        )

    result_pay = result_pay.json()

    reservation_info = request_json.copy()
    reservation_info['startDate'] = reservation_info['startDate'].isoformat()
    reservation_info['endDate'] = reservation_info['endDate'].isoformat()

    sub_request = {
        'reservation_info': reservation_info,
        'user_info': result_loyalty,
        'payment_info': result_pay
    }

    result_reservations = requests.post(
        f'{reserve_service}:{res_service_port}{reserve_service_path}/reserve_hotel',
        data=json.dumps(sub_request)
    )

    if result_reservations.status_code != 201:
        return make_response(
            {'message': 'Reserve service returned'},
            result_reservations.status_code
        )

    result_loyalty = requests.patch(
        f'{loyalty_service}{loy_service_port}{loyalty_service_path}/increment_count_reservations/{user_uuid}'
    )

    if result_loyalty.status_code != 202:
        return make_response(
            {'message': 'Loyalty service returned'},
            result_loyalty.status_code
        )

    total_result = result_reservations.json()
    total_result['discount'] = loyalty_discount
    total_result['payment'] = result_pay

    total_result['hotelUid'] = total_result['hotel_id']['hotel_uid']
    total_result['reservationUid'] = total_result['reservation_uid']
    del total_result['reservation_uid']
    total_result['startDate'] = total_result['start_date']
    total_result['endDate'] = total_result['end_data']
    del total_result['start_date'], total_result['end_data']

    return make_response(
        total_result,
        200
    )


@flask_blueprint.route(base_path + '/reservations/<reservation_uid>', methods=['GET'])
def get_info_about_reservation(reservation_uid=None):
    user_uuid = request.headers.get('X-User-Name')

    if user_uuid is None or len(user_uuid) == 0:
        return make_response(
            {'message': 'Empty header X-User-Name'},
            400
        )

    result_reservations = requests.get(
        f'{reserve_service}{res_service_port}{reserve_service_path}/reservation_info/{reservation_uid}',
        data={
            'user_name': user_uuid
        }
    )

    if result_reservations.status_code != 200:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_reservations.status_code
        )

    total_result = result_reservations.json()

    result_payment = requests.get(
        f'{payment_service}{pay_service_port}{payment_service_path}/payment/{total_result["payment_uid"]}'
    )

    if result_reservations.status_code != 200:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_reservations.status_code
        )

    total_result["payment"] = result_payment.json()

    return make_response(
        total_result,
        200
    )


@flask_blueprint.route(base_path + '/reservations/<reservation_uid>', methods=['DELETE'])
def delete_reservation(reservation_uid=None):
    user_uuid = request.headers.get('X-User-Name')

    if user_uuid is None or len(user_uuid) == 0:
        return make_response(
            {'message': 'Empty header X-User-Name'},
            400
        )

    result_reservations = requests.get(
        f'{reserve_service}{res_service_port}{reserve_service_path}/reservation_info/{reservation_uid}',
        data={
            'user_name': user_uuid
        }
    )

    if result_reservations.status_code != 200:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_reservations.status_code
        )

    result_reservations = result_reservations.json()

    if len(result_reservations.keys()) == 0:
        return make_response(
            {'message': 'Reservation not found'},
            404
        )

    # payment_uid = result_reservations['payment_uid']

    result_payment = requests.delete(
        f'{payment_service}{pay_service_port}{payment_service_path}/payment/{result_reservations["payment_uid"]}'
    )

    if result_payment.status_code != 204:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_payment.status_code
        )

    result_reservation = requests.delete(
        f'{reserve_service}{res_service_port}{reserve_service_path}/reservation_info/{reservation_uid}',
        data={
            'user_name': user_uuid
        }
    )

    if result_reservation.status_code != 204:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_reservation.status_code
        )

    result_loyalty = requests.patch(
        f'{loyalty_service}{loy_service_port}{loyalty_service_path}/decrement_count_reservations/{user_uuid}'
    )

    if result_loyalty.status_code != 202:
        return make_response(
            {'message': 'Loyalty service returned'},
            result_loyalty.status_code
        )

    return make_response(
        '',
        204
    )


@flask_blueprint.route(base_path + '/loyalty', methods=['GET'])
def get_info_about_loyalty(reservation_uid=None):
    user_uuid = request.headers.get('X-User-Name')

    if user_uuid is None or len(user_uuid) == 0:
        return make_response(
            {'message': 'Empty header X-User-Name'},
            400
        )

    result_loyalty = requests.get(
        f'{loyalty_service}{loy_service_port}{loyalty_service_path}/user_info/{user_uuid}'
    )

    if result_loyalty.status_code != 200:
        return make_response(
            {'message': 'Smth is incorrect'},
            result_loyalty.status_code
        )

    result_loyalty = result_loyalty.json()

    return make_response(
        result_loyalty,
        200
    )


