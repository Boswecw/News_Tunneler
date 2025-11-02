"""User model for authentication and authorization."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from .base import Base
import enum


class UserRole(str, enum.Enum):
    """User roles for role-based access control."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    
    # Role-based access control
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_analyst(self) -> bool:
        """Check if user has analyst role or higher."""
        return self.role in [UserRole.ADMIN, UserRole.ANALYST]
    
    @property
    def can_write(self) -> bool:
        """Check if user can write data (admin or analyst)."""
        return self.is_analyst
    
    @property
    def can_read(self) -> bool:
        """Check if user can read data (all active users)."""
        return self.is_active

