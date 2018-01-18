from sqlalchemy import Column
from sqlalchemy.orm.attributes import InstrumentedAttribute

from sqlalchemy_utils import UUIDType
from directorofme import orm

def test__Model_contract():
    class ConcreteModel(orm.Model):
        __tablename__ = "concrete_model"

    assert isinstance(ConcreteModel.id, InstrumentedAttribute), "id is a column"
    assert isinstance(ConcreteModel.id.type, UUIDType), "id is a uuid"
