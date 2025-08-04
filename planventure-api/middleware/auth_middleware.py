from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import (
    verify_jwt_in_request, 
    get_jwt_identity, 
    get_jwt,
    jwt_required
)
from models import User
import time
from collections import defaultdict, deque

class AuthMiddleware:
    """Authentication middleware for route protection."""
    
    # Rate limiting storage (in production, use Redis)
    _rate_limit_storage = defaultdict(deque)
    
    @staticmethod
    def get_current_user():
        """Get current authenticated user."""
        try:
            user_id = get_jwt_identity()
            if user_id:
                user = User.query.get(user_id)
                if user and user.is_active:
                    return user
            return None
        except:
            return None
    
    @staticmethod
    def validate_token():
        """Validate JWT token and return user info."""
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            claims = get_jwt()
            
            # Get user from database
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return None, {'error': 'User not found or inactive'}
            
            # Store user in Flask's g object for request context
            g.current_user = user
            g.current_user_claims = claims
            
            return user, None
            
        except Exception as e:
            return None, {'error': f'Token validation failed: {str(e)}'}
    
    @staticmethod
    def check_admin_permission(user=None):
        """Check if user has admin permissions."""
        if not user:
            user = AuthMiddleware.get_current_user()
        
        if not user:
            return False
        
        return user.is_admin
    
    @staticmethod
    def rate_limit_check(identifier, max_requests=100, window_seconds=3600):
        """
        Check rate limiting for an identifier.
        
        Args:
            identifier (str): Unique identifier (IP, user_id, etc.)
            max_requests (int): Maximum requests allowed
            window_seconds (int): Time window in seconds
            
        Returns:
            tuple: (is_allowed: bool, remaining: int, reset_time: int)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Get or create request history for this identifier
        request_history = AuthMiddleware._rate_limit_storage[identifier]
        
        # Remove old requests outside the window
        while request_history and request_history[0] < window_start:
            request_history.popleft()
        
        # Check if limit exceeded
        if len(request_history) >= max_requests:
            oldest_request = request_history[0]
            reset_time = int(oldest_request + window_seconds)
            return False, 0, reset_time
        
        # Add current request
        request_history.append(now)
        
        remaining = max_requests - len(request_history)
        reset_time = int(now + window_seconds)
        
        return True, remaining, reset_time

# Decorator functions for route protection

def require_auth(f):
    """
    Decorator to require authentication for a route.
    
    Usage:
    @require_auth
    def protected_route():
        # Access current user via g.current_user
        return jsonify({'user': g.current_user.to_dict()})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user, error = AuthMiddleware.validate_token()
        
        if error:
            return jsonify(error), 401
        
        if not user:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please provide a valid access token'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """
    Decorator to require admin privileges for a route.
    
    Usage:
    @require_admin
    def admin_only_route():
        return jsonify({'message': 'Admin access granted'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user, error = AuthMiddleware.validate_token()
        
        if error:
            return jsonify(error), 401
        
        if not user:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please provide a valid access token'
            }), 401
        
        if not AuthMiddleware.check_admin_permission(user):
            return jsonify({
                'error': 'Admin access required',
                'message': 'Insufficient privileges'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """
    Decorator for optional authentication.
    Route works with or without authentication, but user info is available if authenticated.
    
    Usage:
    @optional_auth
    def public_with_optional_auth():
        if hasattr(g, 'current_user') and g.current_user:
            return jsonify({'message': f'Hello {g.current_user.email}'})
        else:
            return jsonify({'message': 'Hello anonymous user'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user, error = AuthMiddleware.validate_token()
            # Don't return error for optional auth, just set user if available
            if user:
                g.current_user = user
        except:
            # Ignore authentication errors for optional auth
            pass
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(max_requests=100, window_seconds=3600, per='ip'):
    """
    Decorator for rate limiting routes.
    
    Args:
        max_requests (int): Maximum requests allowed
        window_seconds (int): Time window in seconds
        per (str): Rate limit per 'ip', 'user', or custom identifier
    
    Usage:
    @rate_limit(max_requests=10, window_seconds=60, per='ip')
    def limited_route():
        return jsonify({'message': 'Rate limited route'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine identifier based on 'per' parameter
            if per == 'ip':
                identifier = request.remote_addr
            elif per == 'user':
                try:
                    user_id = get_jwt_identity()
                    identifier = f"user_{user_id}" if user_id else request.remote_addr
                except:
                    identifier = request.remote_addr
            else:
                identifier = per  # Custom identifier
            
            # Check rate limit
            is_allowed, remaining, reset_time = AuthMiddleware.rate_limit_check(
                identifier, max_requests, window_seconds
            )
            
            if not is_allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Try again later.',
                    'reset_time': reset_time
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(reset_time)
            
            return response
        
        return decorated_function
    return decorator

def cors_middleware(f):
    """
    Decorator to add CORS headers to a route.
    
    Usage:
    @cors_middleware
    def api_route():
        return jsonify({'data': 'value'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        if hasattr(response, 'headers'):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
    
    return decorated_function

def validate_json_request(required_fields=None):
    """
    Decorator to validate JSON request data.
    
    Args:
        required_fields (list): List of required field names
    
    Usage:
    @validate_json_request(['email', 'password'])
    def register():
        data = request.get_json()
        # data is guaranteed to have email and password fields
        return jsonify({'message': 'Valid request'})
    """
    if required_fields is None:
        required_fields = []
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if request has JSON data
            if not request.is_json:
                return jsonify({
                    'error': 'Invalid request format',
                    'message': 'Request must be JSON'
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'No data provided',
                    'message': 'Request body cannot be empty'
                }), 400
            
            # Check required fields
            missing_fields = []
            for field in required_fields:
                if field not in data or not data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Application-level middleware
class RequestMiddleware:
    """Application-level middleware for all requests."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Run before each request."""
        # Add request timestamp
        g.request_start_time = time.time()
        
        # Add request ID for logging
        g.request_id = f"{int(time.time())}-{id(request)}"
        
        # Log request info (in production, use proper logging)
        if current_app.debug:
            print(f"[{g.request_id}] {request.method} {request.path}")
    
    def after_request(self, response):
        """Run after each request."""
        # Add processing time header
        if hasattr(g, 'request_start_time'):
            processing_time = time.time() - g.request_start_time
            response.headers['X-Processing-Time'] = f"{processing_time:.3f}s"
        
        # Add request ID to response
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        return response