from sqlalchemy import BigInteger, String, ForeignKey, Text, Integer, Boolean, Float, func, Date, Column, Enum, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, and_, or_
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio
import enum
from datetime import datetime


engine = create_async_engine('postgresql+asyncpg://postgres:root@localhost:5432/tgk')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    ...


class Proxy(Base):
    __tablename__ = 'proxies'
    
    id = Column(String, primary_key=True)
    version = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(String, nullable=False)
    user = Column(String, nullable=False)
    password = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    date_end = Column(DateTime, nullable=False)
    active = Column(Boolean, nullable=False)
    country = Column(String, nullable=False)
    is_linked = Column(Boolean, nullable=False, default=False)
    

class TelegramAccount(Base):
    __tablename__ = 'telegram_accounts'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=True)
    phone_number_id = Column(Integer, ForeignKey('phone_numbers.id'), unique=True, nullable=False)
    proxy_id = Column(String, ForeignKey('proxies.id'), unique=True, nullable=True)  # Исправлено на String
    gender = Column(String(1), nullable=False)
    description = Column(Text, nullable=True)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    api_id = Column(String, nullable=False)
    api_hash = Column(String, nullable=False)
    is_searcher = Column(Boolean, default=False)
    is_connected = Column(Boolean, default=False)
    auth_code = Column(String(255), nullable=True)
    current_order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    avatar_url = Column(String, nullable=True)
    phone_number = relationship('PhoneNumber', backref='telegram_account')
    proxy = relationship('Proxy', backref='telegram_account')
    current_order = relationship('Order', backref='accounts')



class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    channel_address = Column(String, nullable=False)
    channel_description = Column(Text, nullable=True)
    channel_category = Column(String(255), nullable=True)
    
    ordered_comment_posts = Column(Integer, nullable=True)
    completed_comment_posts = Column(Integer, nullable=True, default=0)
    
    ordered_ad_days = Column(Integer, nullable=True)
    completed_ad_days = Column(Integer, nullable=True, default=0)
    
    accounts_count = Column(Integer, default=0)
    ordered_status = Column(String(255), default='pending') # Active. Completed. Pending.

    is_active = Column(Boolean, default=True, nullable=False)
    

class PhoneNumber(Base):
    __tablename__ = 'phone_numbers'

    id = Column(Integer, primary_key=True)
    number = Column(String(20), unique=True, nullable=False)
    country = Column(String(100), nullable=False)
    is_used = Column(Boolean, default=False)
    received_code = Column(String(10), nullable=True)


class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True)
    telegram_link = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=True)


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    telegram_account_id = Column(Integer, ForeignKey('telegram_accounts.id'), nullable=False)
    channel_link = Column(String(100), nullable=False)
    comment_link = Column(String(100), nullable=True)
    text = Column(Text, nullable=False)
    posted_at = Column(DateTime, nullable=False)

    telegram_account = relationship('TelegramAccount', backref='comments')


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
