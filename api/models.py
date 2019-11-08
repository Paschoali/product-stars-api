from api import db
from marshmallow import Schema, fields
from uuid import uuid4
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import UUIDType
import datetime

Base = declarative_base()
Base.query = db.session.query_property()


class Person(db.Model):
    __tablename__ = 'person'
    id = db.Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    product_list_id = db.relationship('ProductList', backref='person')
    create_date = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)


class ProductList(db.Model):
    __tablename__ = 'productlist'
    person_id = db.Column(UUIDType(binary=False), db.ForeignKey('person.id'), primary_key=True)
    product_id = db.Column(UUIDType(binary=False), primary_key=True)
    insert_date = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)

    __table_args__ = (
        db.PrimaryKeyConstraint(
            person_id,
            product_id
        ), {}
    )


class PersonSchema(Schema):
    id = fields.UUID()
    name = fields.Str()
    email = fields.Email()
    create_date = fields.DateTime()


class ProductSchema(Schema):
    person_id = fields.UUID()
    product_id = fields.UUID()
    insert_date = fields.DateTime()
