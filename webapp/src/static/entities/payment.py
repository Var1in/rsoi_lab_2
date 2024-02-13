from . import *


class Payment(BaseModel):
    id = AutoField(primary_key=True)
    payment_uid = UUIDField(null=False)
    status = CharField(max_length=20)
    price = IntegerField(null=False)
