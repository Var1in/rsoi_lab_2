import json
from uuid import uuid4

from flask import make_response, request
from playhouse.shortcuts import model_to_dict

from . import payment_service_path
from .. import routes
from ..entities.payment import Payment

flask_blueprint = routes


@flask_blueprint.route(payment_service_path + '/payments', methods=['GET'])
def get_all_payments():
    return make_response({}, 200)


@flask_blueprint.route(payment_service_path + '/payment/<payment_uid>', methods=['GET'])
def get_payment_by_id(payment_uid=None):
    payment = Payment.get(Payment.payment_uid == payment_uid)
    return make_response(model_to_dict(payment), 200)


@flask_blueprint.route(payment_service_path + '/payment/<payment_uid>', methods=['DELETE'])
def delete_payment_by_id(payment_uid=None):
    payment = Payment.get(Payment.payment_uid == payment_uid)
    payment.status = 'CANCELED'
    payment.save()
    return make_response('', 204)


@flask_blueprint.route(payment_service_path + '/set_pay', methods=['POST'])
def make_pay():

    if len(request.data) == 0:
        request_json = request.form.to_dict()
    else:
        request_json = json.loads(request.data)

    new_pay = Payment()
    new_pay.payment_uid = uuid4()
    new_pay.price = int(request_json['price'])
    new_pay.status = 'PAID'
    new_pay.save()

    return make_response(model_to_dict(new_pay), 201)

