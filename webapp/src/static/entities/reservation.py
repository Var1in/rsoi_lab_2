from . import *
from .hotels import Hotels


class Reservation(BaseModel):
    id = AutoField(primary_key=True)
    reservation_uid = UUIDField(null=False)
    username = CharField(max_length=80)
    payment_uid = UUIDField(null=False)
    hotel_id = ForeignKeyField(Hotels, to_field='id')
    status = CharField(max_length=20, null=False)
    start_date = DateTimeField(null=False)
    end_data = DateTimeField(null=False)

