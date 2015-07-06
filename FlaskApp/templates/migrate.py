from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, BLOB, func, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound, ObjectDeletedError
from sqlalchemy import create_engine


engine = create_engine(other_info.DB_connection)

