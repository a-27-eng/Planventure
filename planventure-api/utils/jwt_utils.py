from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    decode_token, 
    get_jwt_identity,
    get_jwt,
    verify_jwt_in_request
)
from datetime import datetime, timedelta
import jwt as pyjwt
from functools import wraps
from flask import current_app, jsonify

class JWTUtils:
    """Utility class for JWT token operations."""
    
    @staticmethod
    def generate_tokens(user_id, additional_claims=None):
        """Generate access and refresh tokens for a user."""
        if additional_claims is None:
            additional_claims = {}
        
        additional_claims['iat'] = datetime.utcnow()
        
        access_token = create_access_token(
            identity=user_id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=user_id,
            expires_delta=timedelta(days=30)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': 3600,
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }

def jwt_required_custom(optional=False):
    """Custom JWT required decorator."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=optional)
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    'error': 'Authentication required',
                    'message': str(e)
                }), 401
        return decorated_function
    return decorator

def get_current_user_id():
    """Get current user ID from JWT token."""
    try:
        return get_jwt_identity()
    except:
        return None

def get_current_user_claims():
    """Get current user claims from JWT token."""
    try:
        return get_jwt()
    except:
        return {}

def admin_required(f):
    """Decorator that requires admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            if not claims.get('is_admin', False):
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 401
    return decorated_function