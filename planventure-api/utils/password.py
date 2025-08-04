import bcrypt
import secrets
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

class PasswordUtils:
    """Utility class for password hashing and validation."""
    
    @staticmethod
    def generate_salt():
        """Generate a random salt for password hashing."""
        return bcrypt.gensalt()
    
    @staticmethod
    def hash_password_bcrypt(password, salt=None):
        """
        Hash password using bcrypt with optional custom salt.
        
        Args:
            password (str): Plain text password
            salt (bytes, optional): Custom salt. If None, generates new salt.
            
        Returns:
            str: Hashed password
        """
        if salt is None:
            salt = PasswordUtils.generate_salt()
        
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password_bcrypt(password, hashed_password):
        """
        Verify password against bcrypt hash.
        
        Args:
            password (str): Plain text password to verify
            hashed_password (str): Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    @staticmethod
    def hash_password_werkzeug(password):
        """
        Hash password using Werkzeug's security functions.
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: Hashed password
        """
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    @staticmethod
    def verify_password_werkzeug(password, hashed_password):
        """
        Verify password against Werkzeug hash.
        
        Args:
            password (str): Plain text password to verify
            hashed_password (str): Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(hashed_password, password)
    
    @staticmethod
    def generate_secure_token(length=32):
        """
        Generate a secure random token.
        
        Args:
            length (int): Length of the token in bytes
            
        Returns:
            str: Hex-encoded secure token
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def validate_password_strength(password):
        """
        Validate password strength with detailed feedback.
        
        Args:
            password (str): Password to validate
            
        Returns:
            tuple: (is_valid: bool, messages: list)
        """
        messages = []
        is_valid = True
        
        # Length check
        if len(password) < 8:
            messages.append("Password must be at least 8 characters long")
            is_valid = False
        
        if len(password) > 128:
            messages.append("Password must be less than 128 characters long")
            is_valid = False
        
        # Character type checks
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not has_upper:
            messages.append("Password must contain at least one uppercase letter")
            is_valid = False
        
        if not has_lower:
            messages.append("Password must contain at least one lowercase letter")
            is_valid = False
        
        if not has_digit:
            messages.append("Password must contain at least one number")
            is_valid = False
        
        if not has_special:
            messages.append("Password must contain at least one special character")
            is_valid = False
        
        # Common password checks
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            messages.append("Password is too common")
            is_valid = False
        
        if is_valid:
            messages.append("Password meets all requirements")
        
        return is_valid, messages