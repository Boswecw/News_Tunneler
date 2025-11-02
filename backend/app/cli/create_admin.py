"""CLI tool to create an admin user."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.db import SessionLocal, engine
from app.models.base import Base
from app.models.user import User, UserRole
from app.core.auth import get_password_hash
import getpass


def create_admin_user():
    """Create an admin user interactively."""
    print("=" * 60)
    print("News Tunneler - Create Admin User")
    print("=" * 60)
    print()
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Get user input
    email = input("Email: ").strip()
    username = input("Username: ").strip()
    full_name = input("Full Name (optional): ").strip() or None
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm Password: ")
    
    # Validate
    if not email or not username or not password:
        print("❌ Error: Email, username, and password are required")
        return
    
    if password != password_confirm:
        print("❌ Error: Passwords do not match")
        return
    
    if len(password) < 8:
        print("❌ Error: Password must be at least 8 characters")
        return
    
    # Create user
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            print(f"❌ Error: User with email '{email}' or username '{username}' already exists")
            return
        
        # Create admin user
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print()
        print("✅ Admin user created successfully!")
        print()
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Role: {user.role.value}")
        print()
        print("You can now login with these credentials.")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()

