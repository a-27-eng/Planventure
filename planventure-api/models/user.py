from datetime import datetime
from . import db
from utils import PasswordUtils, JWTUtils
import re

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, email, password, is_admin=False):
        self.email = email.lower().strip()
        self.is_admin = is_admin
        self.set_password(password)
    
    def set_password(self, password):
        """Hash and set the password."""
        is_valid, messages = PasswordUtils.validate_password_strength(password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {'; '.join(messages)}")
        
        self.password_hash = PasswordUtils.hash_password_bcrypt(password)
    
    def check_password(self, password):
        """Check password."""
        return PasswordUtils.verify_password_bcrypt(password, self.password_hash)
    
    def generate_tokens(self):
        """Generate JWT tokens."""
        additional_claims = {
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active
        }
        return JWTUtils.generate_tokens(self.id, additional_claims)
    
    def authenticate(self, password):
        """Authenticate user and return tokens."""
        if not self.is_active:
            return None
        
        if self.check_password(password):
            return self.generate_tokens()
        
        return None
    
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.email}>'