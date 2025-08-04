from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User
from utils import PasswordUtils, JWTUtils, get_current_user_id
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint.
    
    Expected JSON:
    {
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'error': 'No data provided'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Check required fields
        if not email or not password:
            return jsonify({
                'error': 'Email and password are required'
            }), 400
        
        # Validate email format
        if not User.validate_email(email):
            return jsonify({
                'error': 'Invalid email format'
            }), 400
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                'error': 'Email already registered'
            }), 409
        
        # Validate password confirmation
        if password != confirm_password:
            return jsonify({
                'error': 'Passwords do not match'
            }), 400
        
        # Validate password strength
        is_valid, messages = PasswordUtils.validate_password_strength(password)
        if not is_valid:
            return jsonify({
                'error': 'Password validation failed',
                'details': messages
            }), 400
        
        # Create new user
        try:
            new_user = User(email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            
            # Generate tokens for immediate login
            tokens = new_user.generate_tokens()
            
            return jsonify({
                'message': 'User registered successfully',
                'user': new_user.to_dict(),
                'tokens': tokens
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Failed to create user',
                'details': str(e)
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': 'Registration failed',
            'details': str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.
    
    Expected JSON:
    {
        "email": "user@example.com",
        "password": "SecurePassword123!"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Check required fields
        if not email or not password:
            return jsonify({
                'error': 'Email and password are required'
            }), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'error': 'Invalid email or password'
            }), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({
                'error': 'Account is deactivated'
            }), 401
        
        # Authenticate user
        tokens = user.authenticate(password)
        if not tokens:
            return jsonify({
                'error': 'Invalid email or password'
            }), 401
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'tokens': tokens
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Login failed',
            'details': str(e)
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'error': 'User not found or inactive'
            }), 404
        
        # Generate new tokens
        tokens = user.generate_tokens()
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'tokens': tokens
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Token refresh failed',
            'details': str(e)
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information.
    """
    try:
        current_user_id = get_current_user_id()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Failed to get user information',
            'details': str(e)
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password.
    
    Expected JSON:
    {
        "current_password": "CurrentPassword123!",
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided'
            }), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Check required fields
        if not current_password or not new_password or not confirm_password:
            return jsonify({
                'error': 'All password fields are required'
            }), 400
        
        # Check password confirmation
        if new_password != confirm_password:
            return jsonify({
                'error': 'New passwords do not match'
            }), 400
        
        # Get current user
        current_user_id = get_current_user_id()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found'
            }), 404
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({
                'error': 'Current password is incorrect'
            }), 401
        
        # Validate new password
        is_valid, messages = PasswordUtils.validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                'error': 'New password validation failed',
                'details': messages
            }), 400
        
        # Update password
        try:
            user.set_password(new_password)
            db.session.commit()
            
            return jsonify({
                'message': 'Password changed successfully'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Failed to change password',
                'details': str(e)
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': 'Password change failed',
            'details': str(e)
        }), 500

@auth_bp.route('/validate-email', methods=['POST'])
def validate_email():
    """
    Validate email format and availability.
    
    Expected JSON:
    {
        "email": "user@example.com"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided'
            }), 400
        
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'error': 'Email is required'
            }), 400
        
        # Validate email format
        if not User.validate_email(email):
            return jsonify({
                'valid': False,
                'error': 'Invalid email format'
            }), 400
        
        # Check if email is available
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'valid': False,
                'error': 'Email already registered'
            }), 409
        
        return jsonify({
            'valid': True,
            'message': 'Email is valid and available'
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Email validation failed',
            'details': str(e)
        }), 500

@auth_bp.route('/validate-password', methods=['POST'])
def validate_password():
    """
    Validate password strength.
    
    Expected JSON:
    {
        "password": "SecurePassword123!"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided'
            }), 400
        
        password = data.get('password', '')
        
        if not password:
            return jsonify({
                'error': 'Password is required'
            }), 400
        
        # Validate password strength
        is_valid, messages = PasswordUtils.validate_password_strength(password)
        
        return jsonify({
            'valid': is_valid,
            'messages': messages
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Password validation failed',
            'details': str(e)
        }), 500