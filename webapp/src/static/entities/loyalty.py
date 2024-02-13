from . import *


class Loyalty(BaseModel):
    id = AutoField(primary_key=True)
    username = CharField(null=False, unique=True)
    reservation_count = IntegerField(default=0, null=False)
    status = CharField(null=False, default='BRONZE')
    discount = IntegerField(null=False)
