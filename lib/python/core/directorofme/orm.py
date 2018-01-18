'''
orm -- a module providing additional shared functionality for SQLAlchemy-based ORMs.

@author: Matt Story <matt.story@directorof.me>
'''
import functools

from sqlalchemy import Column, String
from sqlalchemy_utils import Timestamp, UUIDType, generic_repr

from .auth.orm import PermissionedModel

### The base model
@generic_repr
class Model(PermissionedModel, Timestamp):
    __abstract__ = True
    #: Unique identifier for this object.
    id = Column(UUIDType, primary_key=True)
