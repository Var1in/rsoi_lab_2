from . import *


class Hotels(BaseModel):
    id = AutoField(primary_key=True)
    hotel_uid = UUIDField(null=False)
    name = CharField(max_length=255, null=False)
    country = CharField(max_length=80, null=False)
    city = CharField(max_length=80, null=False)
    address = CharField(max_length=255, null=False)
    stars = IntegerField()
    price = IntegerField(null=False)