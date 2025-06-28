from sqlalchemy import Column, Integer, String, UniqueConstraint, BigInteger, ARRAY, DateTime, func, Boolean
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Brand(Base):
    __tablename__ = 'brands'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(length=5), unique=True)
    action = Column(String(length=255))
    display_value = Column(String(length=255))
    eng_name = Column(String(length=100))

    __table_args__ = (UniqueConstraint('code', name='uq_brand_code'),)


class Model(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(length=5))
    action = Column(String(length=255))
    display_value = Column(String(length=255))
    eng_name = Column(String(length=100))
    brand_id = Column(Integer)

    __table_args__ = (UniqueConstraint('code', 'brand_id', name='uq_code_brand_id'), )


class Generation(Base):
    __tablename__ = 'generations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(length=5))
    action = Column(String(length=255))
    display_value = Column(String(length=255))
    model_id = Column(Integer)
    start_year = Column(Integer)
    end_year = Column(Integer)

    __table_args__ = (UniqueConstraint('code', 'model_id', name='uq_code_model_id'),)


class Modification(Base):
    __tablename__ = 'modifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(length=10))
    action = Column(String(length=255))
    display_value = Column(String(length=255))
    generation_id = Column(Integer)

    __table_args__ = (UniqueConstraint('code', 'generation_id', name='uq_code_generation_id'),)


class Configuration(Base):
    __tablename__ = 'configurations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(length=10))
    action = Column(String(length=255))
    display_value = Column(String(length=255))
    modification_id = Column(Integer)
    count = Column(Integer)

    __table_args__ = (UniqueConstraint('code', 'modification_id', name='uq_code_modification_id'),)


class Tracking(Base):
    __tablename__ = 'tracking'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    configuration_id = Column(Integer)
    release_year = Column(String(length=9))
    mileage = Column(String(length=13))
    price = Column(String(length=19))
    car_ids = Column(ARRAY(BigInteger))
    is_active = Column(Boolean, server_default='0')
    added_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(length=32))
    first_name = Column(String(length=64))
    last_name = Column(String(length=64))
    full_name = Column(String(length=129))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    is_blocked = Column(Boolean, server_default='0')


class CarViewingHistory(Base):
    __tablename__ = 'car_viewing_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    car_id = Column(BigInteger)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
