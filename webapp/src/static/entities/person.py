from . import *


class Person(BaseModel):
    id = AutoField()
    name = TextField()
    age = IntegerField()
    address = TextField()
    work = TextField()
