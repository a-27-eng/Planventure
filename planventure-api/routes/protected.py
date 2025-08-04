from flask import Blueprint, jsonify, g
from middleware import require_auth, require_admin, optional_auth, rate_limit, validate_json_request

protected_bp = Blueprint('protected', __name__, url_prefix='/api/protected')

@protected_bp.route('/user-only', methods=['GET'])
@require_auth
def user_only_route():
    """Route that requires authentication."""
    return jsonify({
        'message': f'Hello {g.current_user.email}!',
        'user': g.current_user.to_dict()
    })

@protected_bp.route('/admin-only', methods=['GET'])
@require_admin
def admin_only_route():
    """Route that requires admin privileges."""
    return jsonify({
        'message': f'Admin access granted for {g.current_user.email}',
        'user': g.current_user.to_dict()
    })

@protected_bp.route('/optional-auth', methods=['GET'])
@optional_auth
def optional_auth_route():
    """Route with optional authentication."""
    if hasattr(g, 'current_user') and g.current_user:
        return jsonify({
            'message': f'Authenticated user: {g.current_user.email}',
            'authenticated': True
        })
    else:
        return jsonify({
            'message': 'Anonymous user',
            'authenticated': False
        })

@protected_bp.route('/rate-limited', methods=['GET'])
@rate_limit(max_requests=5, window_seconds=60, per='ip')
def rate_limited_route():
    """Route with rate limiting (5 requests per minute per IP)."""
    return jsonify({
        'message': 'This route is rate limited to 5 requests per minute'
    })

@protected_bp.route('/validate-data', methods=['POST'])
@validate_json_request(['name', 'email'])
def validate_data_route():
    """Route that validates required JSON fields."""
    from flask import request
    data = request.get_json()
    
    return jsonify({
        'message': 'Data validation passed',
        'received_data': data
    })

@protected_bp.route('/combined-middleware', methods=['POST'])
@require_auth
@rate_limit(max_requests=10, window_seconds=300, per='user')
@validate_json_request(['action'])
def combined_middleware_route():
    """Route with multiple middleware decorators."""
    from flask import request
    data = request.get_json()
    
    return jsonify({
        'message': 'All middleware checks passed',
        'user': g.current_user.email,
        'action': data['action']
    })