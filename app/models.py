from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) 
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  
    links = relationship("Link", back_populates="owner")

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, index=True)
    short_code = Column(String, unique=True, index=True)
    custom_alias = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)  
    project = Column(String, nullable=True)  
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="links")
    stats = relationship("LinkStat", back_populates="link", cascade="all, delete-orphan")

class LinkStat(Base):
    """Модель для хранения статистики переходов по ссылкам"""
    __tablename__ = "link_stats"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"))
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String, nullable=True)  
    user_agent = Column(String, nullable=True)  
    referer = Column(String, nullable=True)  
    country = Column(String, nullable=True) 

    link = relationship("Link", back_populates="stats")