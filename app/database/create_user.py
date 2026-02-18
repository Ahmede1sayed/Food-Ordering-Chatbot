"""
Create test user in database
Run: python create_test_user.py
"""

from app.database.connection import db
from app.models.user import User

def create_test_user():
    """Create a test user with ID 1"""
    session = db.get_session()
    
    try:
        # Check if user already exists
        existing_user = session.query(User).filter(User.id == 1).first()
        
        if existing_user:
            print(f"✅ User already exists: {existing_user.name}")
            return
        
        # Create new user
        user = User(
            id=1,
            name="Test User",
            phone="1234567890",
            address="Test Address"
        )
        
        session.add(user)
        session.commit()
        
        print("✅ Test user created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Phone: {user.phone}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating user: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    create_test_user()