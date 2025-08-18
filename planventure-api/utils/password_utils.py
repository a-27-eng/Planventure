import bcrypt
import re

class PasswordUtils:
    """Utility class for password operations."""
    
    @staticmethod
    def hash_password_bcrypt(password):
        """
        Hash a password using bcrypt.
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: Hashed password
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password_bcrypt(password, hashed_password):
        """
        Verify a password against its hash.
        
        Args:
            password (str): Plain text password
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
    def validate_password_strength(password):
        """
        Validate password strength.
        
        Args:
            password (str): Password to validate
            
        Returns:
            tuple: (is_valid: bool, messages: list)
        """
        messages = []
        is_valid = True
        
        if len(password) < 8:
            messages.append("Password must be at least 8 characters long")
            is_valid = False
        
        if len(password) > 128:
            messages.append("Password must be less than 128 characters")
            is_valid = False
        
        if not re.search(r'[A-Z]', password):
            messages.append("Password must contain at least one uppercase letter")
            is_valid = False
        
        if not re.search(r'[a-z]', password):
            messages.append("Password must contain at least one lowercase letter")
            is_valid = False
        
        if not re.search(r'\d', password):
            messages.append("Password must contain at least one number")
            is_valid = False
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', password):
            messages.append("Password must contain at least one special character")
            is_valid = False
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in weak_passwords:
            messages.append("Password is too common, please choose a stronger password")
            is_valid = False
        
        return is_valid, messages
    
    @staticmethod
    def generate_random_password(length=12):
        """
        Generate a random password.
        
        Args:
            length (int): Length of password to generate
            
        Returns:
            str: Generated password
        """
        import secrets
        import string
        
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest randomly
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)