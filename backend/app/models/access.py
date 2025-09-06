from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.session import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String)

    users = relationship("UserRole", back_populates="role")
    access_rules = relationship("AccessRule", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    created_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class BusinessObject(Base):
    __tablename__ = "business_objects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), default=func.now())

    access_rules = relationship("AccessRule", back_populates="object")


class AccessRule(Base):
    __tablename__ = "access_rules"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    object_id = Column(Integer, ForeignKey("business_objects.id"))
    can_read = Column(Boolean, default=False)
    can_read_all = Column(Boolean, default=False)
    can_create = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_update_all = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_delete_all = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    role = relationship("Role", back_populates="access_rules")
    object = relationship("BusinessObject", back_populates="access_rules")
