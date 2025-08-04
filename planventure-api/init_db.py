import os
import sys
from app import create_app
from models import db, User, Trip

def init_database():
    """Initialize the database with tables."""
    print("=" * 50)
    print("PlanVenture Database Initialization")
    print("=" * 50)
    
    try:
        app = create_app()
        
        with app.app_context():
            # Check if database exists
            db_path = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"Database URI: {db_path}")
            
            # Always drop existing tables to handle schema changes
            print("Dropping existing tables (if any)...")
            db.drop_all()
            print("✓ Existing tables dropped")
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully!")
            
            # Check if we should create a test user
            user_count = User.query.count()
            print(f"Current users in database: {user_count}")
            
            if user_count == 0:
                create_test = input("\nCreate a test user? (Y/n): ").lower()
                if create_test != 'n' and create_test != 'no':
                    # Get user input for test user
                    email = input("Enter test user email (default: test@example.com): ").strip()
                    if not email:
                        email = "test@example.com"
                    
                    password = input("Enter test user password (default: TestPassword123!): ").strip()
                    if not password:
                        password = "TestPassword123!"
                    
                    # Ask if user should be admin
                    is_admin_input = input("Make this user an admin? (y/N): ").lower()
                    is_admin = is_admin_input == 'y' or is_admin_input == 'yes'
                    
                    # Validate email
                    if not User.validate_email(email):
                        print("❌ Invalid email format!")
                        return False
                    
                    # Create test user
                    try:
                        test_user = User(email=email, password=password, is_admin=is_admin)
                        db.session.add(test_user)
                        db.session.commit()
                        print(f"✓ Test user created: {test_user.email} (Admin: {test_user.is_admin})")
                    except Exception as e:
                        print(f"❌ Error creating test user: {str(e)}")
                        db.session.rollback()
                        return False
            
            # Final status
            print("\n" + "=" * 50)
            print("Database initialization completed successfully!")
            print(f"Total users: {User.query.count()}")
            print(f"Total trips: {Trip.query.count()}")
            print("=" * 50)
            return True
            
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False

if __name__ == '__main__':
    init_database()