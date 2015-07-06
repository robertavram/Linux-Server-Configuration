from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base
from other_info import DB_connection
engine = create_engine(DB_connection)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
dbs = DBSession()
