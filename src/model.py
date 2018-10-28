import json
from datetime import datetime as dt
from mongoengine import *

with open('user.config') as f:
    user = json.loads(f.read())

#client = MongoClient(user["mongo_atlas"])
#db = client["IDM"]

connect('IDM', user["mongo_atlas"])


DED_CHOICES = ("fixed amount", "franchise", "% of TIV", "% of limit", "minimum", "maximum")
LIM_CHOICES = ("fixed amount", "% of loss")
COVERED_PERILS = ["EQ", "FL", "WS", "Fire"]

class Address(EmbeddedDocument):
    country = StringField()
    city = StringField()
    street = StringField()
    postal_code = StringField()    


class Account(Document):
    account_id = StringField(required=True)
    name = StringField()
    address = EmbeddedDocumentField(Address)
    email = EmailField()
    #policies = ListField(Policy)
    #insured_objects = ListField(InsuredObject)


class Deductible(EmbeddedDocument):
    type = StringField(choices=DED_CHOICES, required=True)
    value = FloatField(required= True)
    currency = StringField(default="EUR")

    def clean(self):
        if self.type in ["% of TIV", "% of loss"]:
            self.currency = None
            if ((self.value < 0) or (self.value > 1)):
                msg = 'Value must be between 0 and 1'
                raise ValidationError(msg)
        elif self.type in ["fixed amout", "franchise", "minimum", "maximum"]:
            if self.currency == None:
                msg = 'No currency specified'
                raise ValidationError(msg)
            if (self.value < 0):
                msg = 'Value must not be negative'
                raise ValidationError(msg)
            

class Limit(EmbeddedDocument):
    type = StringField(choices=LIM_CHOICES, required=True)
    value = FloatField(required= True)

    def clean(self):
        if self.type in ["% of loss"] and ((self.value < 0) or (self.value > 1)):
            msg = 'Value must be between 0 and 1'
            raise ValidationError(msg)
        elif self.type in ["fixed amout"] and (self.value < 0):
            msg = 'Value must not be negative'
            raise ValidationError(msg)



class Term(EmbeddedDocument):
    deductible = EmbeddedDocumentListField(Deductible)
    limit = EmbeddedDocumentListField(Limit)
    share = FloatField(default=1.0)
    covered_perils = ListField(StringField(), default= COVERED_PERILS)
    def clean(self):
        if (self.share < 0) or (self.share > 1):
            msg = 'Share must be between 0 and 1'
            raise ValidationError(msg)
    

class Layer(Document):
    #layer_id = ObjectIdField(required=True)
    policy = ReferenceField('Policy')
    covered_layers = ListField(ReferenceField('self'))
    covered_insured_objects = ListField(ReferenceField('InsuredObject'))
    feeds_into_layer = ListField(ReferenceField('self'))
    feeds_into_policyloss = BooleanField(default=True)
    terms = EmbeddedDocumentField(Term)
    

class Policy(Document):
    #policy_id = ObjectIdField(required=True)
    account = ReferenceField(Account)
    inception_date = DateTimeField()
    expiration_date = DateTimeField()
    layers = ListField(ReferenceField('Layer'))
    covered_perils = ListField(StringField(length=255), default= lambda: COVERED_PERILS)
            

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
    

class TIV(EmbeddedDocument):
    value = FloatField(default=0.0)
    currency = StringField(default="EUR")
    as_of = DateTimeField(default=dt.now())

    def clean(self):
        if self.value < 0:
            msg= 'TIV must not be negative'
            raise ValidationError(msg)


class Coverage(EmbeddedDocument):
    tiv = EmbeddedDocumentField(TIV)
    terms = EmbeddedDocumentField(Term)


class InsuredObject(Document):
    account = ReferenceField(Account)
    meta = {'allow_inheritance': True}


class Building(InsuredObject):
    occupancy = EmbeddedDocumentField(Occupancy)
    construction = EmbeddedDocumentField(Construction)
    location = PointField()
    address = EmbeddedDocumentField(Address)
    building = EmbeddedDocumentField(Coverage)
    content = EmbeddedDocumentField(Coverage)
    time_element = EmbeddedDocumentField(Coverage)
    other = EmbeddedDocumentField(Coverage)
