from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import create_engine, func

import other_info


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @classmethod
    def get_by_email(cls, dbs, email):
        try:
            myu = dbs.query(cls).filter_by(email=email).one()
            return myu
        except NoResultFound:
            return False

    @classmethod
    def get_by_id(cls, dbs, uid):
        try:
            myu = dbs.query(cls).get(uid)
            return myu
        except NoResultFound:
            return False

    @classmethod
    def delete_user(cls, dbs, uid):
        u = dbs.query(cls).get(uid)
        dbs.delete(u)
        dbs.commit()

    @classmethod
    def get_all(cls, dbs):
        return dbs.query(cls).all()

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'picture': self.picture
        }


class Images(Base):
    __tablename__ = 'images'
    id = Column(String(250), primary_key=True)
    data = Column(LargeBinary, nullable=False)

    @classmethod
    def store_img(cls, dbs, name, img):
        my_img = dbs.query(cls).get(name)
        if my_img:
            return my_img
        my_img = cls(id=name, data=img)
        dbs.add(my_img)
        dbs.commit()

        return my_img

    @classmethod
    def delete_by_id(cls, dbs, imgid):
        r = dbs.query(cls).filter_by(id=imgid).delete()
        dbs.commit()
        return r

    @classmethod
    def delete_all(cls, dbs):
        dbs.query(cls).delete()
        dbs.commit()


class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    category = Column(String(250), nullable=False)
    description = Column(String(1000))
    link = Column(String(250))
    updated_on = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.current_timestamp())
    user_id = Column(Integer, ForeignKey('user.id'))
    picture = Column(String(250), ForeignKey('images.id'))
    user = relationship(User)
    images = relationship(Images, cascade="all")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'id': self.id,
            'link': self.link,
            'user_id': self.user_id,
            'picture': self.picture
        }

    @classmethod
    def get_by_id(cls, dbs, item_id):
        try:
            myi = dbs.query(cls).get(item_id)
            return myi
        except NoResultFound:
            return False

    @classmethod
    def delete_by_id(cls, dbs, item_id):
        my_item = dbs.query(cls).filter_by(id=item_id).first()
        return cls.delete_by_item(dbs, my_item)

    @classmethod
    def delete_by_user(cls, dbs, uid):
        ''' Deletes all items and associated images that belong to a user '''
        user_items = dbs.query(cls).filter_by(user_id=uid)
        # Doing it this way rather than on the query so that it cascades to the
        # images as well
        for item in user_items:
            dbs.delete(item)
        dbs.commit()

    @classmethod
    def delete_by_item(cls, dbs, my_item):
        '''Deletes Item'''
        dbs.delete(my_item)
        dbs.commit()
        return True


    @classmethod
    def update_item(cls, dbs, item):
        dbs.add(item)
        dbs.commit()
        return True

    @classmethod
    def item_exists(cls, dbs, name, category):
        return dbs.query(cls).filter(
            cls.name == name, cls.category == category).first()

    @classmethod
    def addItem(cls, dbs, item_dict):
        my_item = cls(**item_dict)
        dbs.add(my_item)
        dbs.commit()
        return my_item

    @classmethod
    def get_all_w_names(cls, dbs, limit=100):
        return dbs.query(cls.name, cls.category, cls.id, cls.link,
                         cls.user_id, cls.updated_on, cls.picture,
                         cls.description,
                         User.name.label("uname")).filter(cls.user_id == User.id).order_by(cls.updated_on.desc()).limit(limit).all()

    @classmethod
    def get_all_by_user(cls, dbs, uid, limit=100):
        return dbs.query(cls).filter_by(user_id=uid).order_by(
            cls.updated_on.desc()).limit(limit).all()

    @classmethod
    def get_all(cls, dbs):
        return dbs.query(cls).all()

    @classmethod
    def get_by_category_w_names(cls, dbs, category):
        if not category in other_info.item_categories:
            return False
        return dbs.query(cls.name, cls.category, cls.id, cls.link,
                         cls.user_id, cls.updated_on, cls.picture,
                         cls.description,
                         User.name.label("uname")).filter(cls.user_id == User.id, cls.category == category).order_by(cls.name.asc()).all()

    @classmethod
    def get_by_category(cls, dbs, category):
        if not category in other_info.item_categories:
            return False
        return dbs.query(cls).filter_by(
            category=category).order_by(cls.name.asc()).all()

    def add_change_picture(self, dbs, pictureid):
        if self.picture:
            Images.delete_by_id(dbs, self.picture)
        self.picture = pictureid
        dbs.add(self)
        dbs.commit()


engine = create_engine(other_info.DB_connection)


Base.metadata.create_all(engine)
