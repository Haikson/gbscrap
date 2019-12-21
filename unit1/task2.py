#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey,    Date, Float
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.sql import ClauseElement


# In[2]:


CURRENT_PATH = os.path.dirname(os.path.abspath('__file__'))
engine = create_engine('sqlite:///{}'.format(os.path.join(CURRENT_PATH, '..', 'data', '5ka.sqlite')), echo=False)

Model = declarative_base()
Session = scoped_session(sessionmaker(bind=engine, autocommit=True))


# In[3]:


goods_categories = Table('goods_categories', Model.metadata,
    Column('goods_id', Integer, ForeignKey('goods.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class Category(Model):
    __tablename__ = 'categories'
    
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String)
    code = Column('code', String)
    goods = relationship("Goods", secondary=goods_categories, back_populates="categories")
    
    def __init__(self, name, code):
        self.name = name
        self.code = code
        
    def __repr__(self):
        return '<Category ({id}, {name}, {code})>'.format(
            id=self.id, name=self.name, code=self.code)
    
    @property
    def pk(self):
        return self.id
    

class Goods(Model):
    __tablename__ = 'goods'
    
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String)
    mech = Column('mech', String)
    img_link = Column('img_link', String)
    price_reg_min = Column('price_reg_min', Float)
    price_promo_min = Column('price_promo_min', Float)
    promo = Column('promo_id', ForeignKey('promo.id'))
    categories = relationship("Category", secondary=goods_categories, back_populates="goods")
    
    
    def __init__(self, id, name, price_reg_min, price_promo_min, mech=None, img_link=None, promo=None):
        self.id = id
        self.name = name
        self.mech = mech
        self.img_link = img_link
        self.price_reg_min = price_reg_min
        self.price_promo_min = price_promo_min
        self.category=category
        self.promo=promo
        
    def __repr__(self):
        return '<Goods ({id}, {name})>'.format(id=self.id, name=self.name)
    
    @property
    def pk(self):
        return self.id
    

class Promo(Model):
    __tablename__ = 'promo'
    
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String)
    date_begin = Column('date_begin', Date)
    date_end = Column('date_end', Date)
    promo_type = Column('promo_type', String)
    description = Column('description', String)
    kind = Column('kind', String)
    expired_at = Column('expired_at', Integer)
    
    def __init__(self, id, date_begin, date_end, promo_type, description, kind, expired_at):
        self.id = id
        self.date_begin = date_begin
        self.date_end = date_end
        self.promo_type = promo_type
        self.description = description
        self.kind = kind
        self.expired_at = expired_at
        
    def __repr__(self):
        return '<Promo ({id}, {name})>'.format(id=self.id, name=self.name)
    
    @property
    def pk(self):
        return self.id
    
Model.metadata.create_all(engine)


# In[4]:


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


# In[5]:


import requests
import json
from datetime import datetime
import time

class ResponseError(BaseException):
    """
    Class for response exceptions
    """


# In[7]:


def get_page_result(url, try_n=0):
    response = requests.get(url)
    if response.status_code >= 500:
        if try_n < 10:
            time.sleep(3)
            try_n += 1
            return get_page_result(url, try_n)
        else:
            return {}
    elif response.status_code != 200:
        return {}
    return response.json()


# In[8]:


def parse_categories():
    session = Session()
    url = "https://5ka.ru/api/v2/categories/"
    results = get_page_result(url)
    categories = [Category(name=res.get("parent_group_name"), code=res.get("parent_group_code")) for res in results]
    session.add_all(categories)
    return session.query(Category).all()


# In[9]:


def save_result(data, category):
    results = data.get('results', [])
    session = Session()
    for result in results:
        promo_data = result.get("promo", {})
        promo, _ = get_or_create(
            session, Promo, 
            id=promo_data.get('id'),
            date_begin=datetime.strptime(promo_data.get("date_begin"), "%Y-%m-%d").date(),
            date_end=datetime.strptime(promo_data.get("date_end"), "%Y-%m-%d").date(),
            promo_type=promo_data.get("promo_type"),
            description=promo_data.get("description"),
            kind=promo_data.get("kind"),
            expired_at=promo_data.get("expired_at")
        )
        
        goods, _ = get_or_create(
            session, Goods,
            id=result.get("id"),
            name=result.get("name"),
            mech=result.get("mech"),
            img_link=result.get("img_link"),
            price_reg_min=result.get("price_reg_min"),
            price_promo_min=result.get("price_promo_min"),
            promo=promo.pk
        )
        goods.categories.append(category)


# In[10]:


def parse_goods(next_page, category):
    while next_page is not None:
        result = get_page_result(start_url)
        save_result(result, category)
        next_page = result.get('next')
        time.sleep(3)
        


# In[11]:


categories = parse_categories()
categories[0].name, categories[0].code


# In[12]:


session=Session()
start_urls = {
    "https://5ka.ru/api/v2/special_offers/?records_per_page=20&page=1&categories={category}".format(
        category=category.code
    ): category
    for category in session.query(Category)
}


# In[ ]:


for start_url, category in start_urls.items():
    parse_goods(start_url, category)
    


# In[ ]:


goods_count = session.query(Goods).count()
print(goods_count)


# In[ ]:


engine.dispose()

