import json
from mongoengine import *

with open('../user.config') as f:
    user = json.loads(f.read())

#client = MongoClient(user["mongo_atlas"])
#db = client["IDM"]

connect('IDM', user["mongo_atlas"])


class Account(Document):
    account_id = StringField(required=True)
    name = StringField()
    address = EmbeddedDocumentField(Address)
    email = StringField()
    #policies = ListField(Policy)
    #insured_objects = ListField(InsuredObject)


class Term(EmbeddedDocument):
    

class Layer(Document):
    layer_id = ObjectIdField(required=True)
    covers = ListField(ReferenceField(Layer))
    feeds_into = ListField(ReferenceField(Layer))
    terms = 
    

class Policy(Document):
    policy_id = ObjectIdField(required=True)
    account = ReferenceField(Account)
    

class Address(EmbeddedDocument):
    country = StringField()
    city = StringField()
    street = StringField()
    postal_code = StringField()    
    

class Geometry(EmbeddedDocument):
    geomtype = StringField()
    coordinates = ListField()
    

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
    geometry = EmbeddedDocumentField(Geometry)
    iotype = StringField()
    
    meta = {'allow_inheritance': True}


class Building(InsuredObject):
    occupancy = EmbeddedDocumentField(Occupancy)
    construction = EmbeddedDocumentField(Construction)
    

