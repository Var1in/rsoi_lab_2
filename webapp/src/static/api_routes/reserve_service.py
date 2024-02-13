import json
from datetime import datetime
from uuid import uuid4

from flask import make_response, request
from playhouse.shortcuts import model_to_dict

from . import reserve_service_path
from .. import routes
from ..entities.hotels import Hotels
from ..entities.reservation import Reservation

flask_blueprint = routes


@flask_blueprint.route(reserve_service_path + '/hotels', methods=['GET'])
def get_all_hotels():
    params = request.args
    page = int(params.get('page', 1))
    size = int(params.get('size', 1))

    hotels = Hotels.select().dicts()

    result = [
        value for value in hotels
    ]

    result = result[((page - 1) * size):(page * size)]

    for value in result:
        value['hotelUid'] = value['hotel_uid']

    response = {
        "page": page,
        "pageSize": size,
        "totalElements": len(result),
        "items": result
    }

    return make_response(
        response,
        200)


@flask_blueprint.route(reserve_service_path + '/user_info/<user_uuid>')
def get_info_by_user_id(user_uuid=None):
    if user_uuid is None:
        return make_response(
            {'message': 'Empty response'},
            400
        )
    reservations = Reservation.select().join(Hotels).where(Reservation.username == user_uuid).dicts()
    result = []
    for reservation in reservations:
        hotel = Hotels.get(Hotels.id == reservation['hotel_id'])

        data = reservation
        data['hotel'] = model_to_dict(hotel)

        data['reservationUid'] = data['reservation_uid']
        data['startDate'] = data['start_date'].strftime("%Y-%m-%d")
        data['endDate'] = data['end_data'].strftime("%Y-%m-%d")
        data['hotel']['hotelUid'] = data['hotel']['hotel_uid']
        data['hotel']['fullAddress'] = (
                data['hotel']['country']
                + ', ' + data['hotel']['city']
                + ', ' + data['hotel']['address']
        )

        del (
            data['start_date'],
            data['end_data'],
            data['reservation_uid'],
            data['hotel']['hotel_uid']
        )

        result.append(
            data
        )
    return result


@flask_blueprint.route(reserve_service_path + '/hotel_price/<hotel_uuid>')
def get_hotel_price(hotel_uuid=None):
    if hotel_uuid is None:
        return make_response(
            {'message': 'Empty response'},
            400
        )
    hotel = Hotels.get(Hotels.hotel_uid == hotel_uuid)
    return {
        'price': hotel.price
    }


@flask_blueprint.route(reserve_service_path + '/reserve_hotel', methods=['POST'])
def reserve_hotel_service():
    if len(request.data) != 0:
        request_json = json.loads(request.data)
    else:
        request_json = request.form.to_dict()

    reservation_info = request_json['reservation_info']
    hotel_uuid = reservation_info['hotelUid']
    start_date = datetime.fromisoformat(reservation_info['startDate'])
    end_date = datetime.fromisoformat(reservation_info['endDate'])

    user_info = request_json['user_info']
    username = user_info['username']

    payment_info = request_json['payment_info']
    payment_uid = payment_info['payment_uid']

    hotel = Hotels.get(Hotels.hotel_uid == hotel_uuid)
    hotel = model_to_dict(hotel)

    reserve_row = Reservation()
    reserve_row.reservation_uid = uuid4()
    reserve_row.username = username
    reserve_row.status = 'PAID'
    reserve_row.payment_uid = payment_uid
    reserve_row.start_date = start_date
    reserve_row.end_data = end_date
    reserve_row.hotel_id = hotel['id']
    reserve_row.save()

    reserve_row.start_date = start_date.strftime("%Y-%m-%d")
    reserve_row.end_data = end_date.strftime("%Y-%m-%d")

    return make_response(model_to_dict(reserve_row), 201)


@flask_blueprint.route(reserve_service_path + '/reservation_info/<reservation_uid>', methods=['GET'])
def get_reservation_info(reservation_uid=None):
    if len(request.data) != 0:
        request_json = json.loads(request.data)
    else:
        request_json = request.form.to_dict()

    # reservations = Reservation.select().join(Hotels).where(Reservation.username == user_uuid).dicts()
    reservations = Reservation.select(Reservation).where(Reservation.reservation_uid == reservation_uid).dicts()

    reservation = [value for value in reservations]
    if len(reservations) == 0:
        return make_response({'message': 'Билет не найден'}, 404)

    reservation = reservation[0]

    hotel_id = reservation['hotel_id']

    hotel = Hotels.get(Hotels.id == hotel_id)

    reservation['hotel'] = model_to_dict(hotel)

    reservation['reservationUid'] = reservation['reservation_uid']
    reservation['startDate'] = reservation['start_date'].strftime("%Y-%m-%d")
    reservation['endDate'] = reservation['end_data'].strftime("%Y-%m-%d")
    reservation['hotel']['hotelUid'] = reservation['hotel']['hotel_uid']
    reservation['hotel']['fullAddress'] = (
            reservation['hotel']['country']
            + ', ' + reservation['hotel']['city']
            + ', ' + reservation['hotel']['address']
    )

    del (
        reservation['start_date'],
        reservation['end_data'],
        reservation['reservation_uid'],
        reservation['hotel']['hotel_uid']
    )

    return make_response(reservation, 200)


@flask_blueprint.route(reserve_service_path + '/reservation_info/<reservation_uid>', methods=['DELETE'])
def delete_reservation_service(reservation_uid=None):
    if len(request.data) != 0:
        request_json = json.loads(request.data)
    else:
        request_json = request.form.to_dict()

    reservation = Reservation.get(Reservation.reservation_uid == reservation_uid)

    reservation.status = 'CANCELED'
    reservation.save()

    return make_response('', 204)
