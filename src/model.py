import json
from mongoengine import *

with open('../user.config') as f:
    user = json.loads(f.read())

#client = MongoClient(user["mongo_atlas"])
#db = client["IDM"]

connect('IDM', user["mongo_atlas"])


DED_CHOICES = ("fixed amount", "franchise", "% of TIV", "% of limit", "minimum", "maximum")
LIM_CHOICES = ("fixed amount", "% of loss")

class Account(Document):
    account_id = StringField(required=True)
    name = StringField()
    address = EmbeddedDocumentField(Address)
    email = StringField()
    #policies = ListField(Policy)
    #insured_objects = ListField(InsuredObject)


class Deductible(EmbeddedDocument):
    type = StringField(choices=DED_CHOICES, required=True)
    value = FloatField(required= True)


class Limit(EmbeddedDocument):
    type = StringField(choices=LIM_CHOICES, required=True)
    value = FloatField(required= True)


class Term(EmbeddedDocument):
    deductible = EmbeddedDocumentListField(Deductible)
    limit = EmbeddedDocumentListField(Limit)
    share = FloatField
    

class Layer(Document):
    #layer_id = ObjectIdField(required=True)
    policy = ReferenceField('Policy')
    covers = ListField(ReferenceField('self'))
    feeds_into = ListField(ReferenceField('self'))
    terms = EmbeddedDocumentField(Term)
    

class Policy(Document):
    #policy_id = ObjectIdField(required=True)
    account = ReferenceField(Account)
    inception_date = DateTimeField()
    expiration_date = DateTimeField()
    layers = ListField(ReferenceField('Layer'))
    

class Address(EmbeddedDocument):
    country = StringField()
    city = StringField()
    street = StringField()
    postal_code = StringField()    
        

class Occupancy(EmbeddedDocument):
    classification = StringField(default="ATC")
    occupancy_class = StringField(default="0")
    description = StringField()


class Construction(EmbeddedDocument):
    classification = StringField(default="ATC")
    construction_class = StringField()
    description = StringField()
    year_built = IntField()
    height = IntField()
    

class InsuredObject(Document):
    account = ReferenceField(Account)
    address = EmbeddedDocumentField(Address)
    location = PointField()
    iotype = StringField()
    
    meta = {'allow_inheritance': True}


class Building(InsuredObject):
    occupancy = EmbeddedDocumentField(Occupancy)
    construction = EmbeddedDocumentField(Construction)
    

