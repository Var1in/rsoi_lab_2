from flask import make_response
from playhouse.shortcuts import model_to_dict

from src.static.entities.loyalty import Loyalty
from . import loyalty_service_path
from .. import routes

flask_blueprint = routes


@flask_blueprint.route(loyalty_service_path + '/loyalty', methods=['GET'])
def get_all_loyalty():
    return make_response({}, 200)


@flask_blueprint.route(loyalty_service_path + '/user_info/<user_uuid>')
def get_user_loyalty_info(user_uuid=None):
    if user_uuid is None:
        return make_response(
            {'message': 'Empty response'},
            400
        )

    res_loyalty = Loyalty.get(Loyalty.username == user_uuid)

    res_loyalty = model_to_dict(res_loyalty)
    res_loyalty['reservationCount'] = res_loyalty['reservation_count']
    del res_loyalty['reservation_count']

    return make_response(
        res_loyalty,
        200
    )


@flask_blueprint.route(loyalty_service_path + '/increment_count_reservations/<user_uuid>', methods=['PATCH'])
def increment_count_reservations(user_uuid=None):
    if user_uuid is None:
        return make_response(
            {'message': 'Empty response'},
            400
        )

    res_loyalty = Loyalty.get(Loyalty.username == user_uuid)
    res_loyalty.reservation_count += 1
    if res_loyalty.reservation_count == 11:
        res_loyalty.status = 'SILVER'
        res_loyalty.discount = 7
    elif res_loyalty.reservation_count == 21:
        res_loyalty.status = 'GOLD'
        res_loyalty.discount = 10
    res_loyalty.save()

    return make_response(
        model_to_dict(res_loyalty),
        202
    )


@flask_blueprint.route(loyalty_service_path + '/decrement_count_reservations/<user_uuid>', methods=['PATCH'])
def decrement_count_reservations(user_uuid=None):
    if user_uuid is None:
        return make_response(
            {'message': 'Empty response'},
            400
        )

    res_loyalty = Loyalty.get(Loyalty.username == user_uuid)
    res_loyalty.reservation_count -= 1
    if res_loyalty.reservation_count == 10:
        res_loyalty.status = 'BRONZE'
        res_loyalty.discount = 5
    elif res_loyalty.reservation_count == 20:
        res_loyalty.status = 'SILVER'
        res_loyalty.discount = 7
    res_loyalty.save()

    return make_response(
        model_to_dict(res_loyalty),
        202
    )
