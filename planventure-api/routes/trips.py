from flask import Blueprint, request, jsonify, g
from datetime import datetime, date
from models import db, Trip, User
from middleware import require_auth, optional_auth, rate_limit, validate_json_request
from utils import get_current_user_id, ItineraryGenerator
import json

trips_bp = Blueprint('trips', __name__, url_prefix='/api/trips')

@trips_bp.route('/', methods=['GET'])
@optional_auth
def get_trips():
    """Get all trips (with optional filtering)."""
    try:
        # Get query parameters
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status', '').strip()
        destination = request.args.get('destination', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        # Base query
        query = Trip.query
        
        # Apply filters
        if user_id:
            # Only admin can filter by other user's ID
            current_user_id = get_current_user_id()
            if current_user_id != user_id:
                current_user = User.query.get(current_user_id) if current_user_id else None
                if not current_user or not current_user.is_admin:
                    return jsonify({
                        'error': 'Unauthorized to view other users trips'
                    }), 403
            query = query.filter(Trip.user_id == user_id)
        elif hasattr(g, 'current_user') and g.current_user:
            # If authenticated, show only user's trips
            query = query.filter(Trip.user_id == g.current_user.id)
        else:
            # If not authenticated, show no trips
            return jsonify({
                'trips': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'message': 'Login to view your trips'
            }), 200
        
        if status:
            query = query.filter(Trip.status == status)
        
        if destination:
            query = query.filter(Trip.destination.ilike(f'%{destination}%'))
        
        # Order by creation date (newest first)
        query = query.order_by(Trip.created_at.desc())
        
        # Paginate
        trips_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        trips_data = [trip.to_dict() for trip in trips_paginated.items]
        
        return jsonify({
            'trips': trips_data,
            'total': trips_paginated.total,
            'page': page,
            'per_page': per_page,
            'total_pages': trips_paginated.pages,
            'has_next': trips_paginated.has_next,
            'has_prev': trips_paginated.has_prev
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve trips',
            'details': str(e)
        }), 500

@trips_bp.route('/', methods=['POST'])
@require_auth
@rate_limit(max_requests=20, window_seconds=3600, per='user')
@validate_json_request(['title', 'destination', 'start_date', 'end_date'])
def create_trip():
    """Create a new trip."""
    try:
        data = request.get_json()
        
        # Extract required fields
        title = data.get('title', '').strip()
        destination = data.get('destination', '').strip()
        start_date_str = data.get('start_date', '').strip()
        end_date_str = data.get('end_date', '').strip()
        
        # Validate required fields
        if not title or not destination or not start_date_str or not end_date_str:
            return jsonify({
                'error': 'Title, destination, start_date, and end_date are required'
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Validate dates
        is_valid, message = Trip.validate_dates(start_date, end_date)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Extract optional fields
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        description = data.get('description', '').strip()
        budget = data.get('budget')
        itinerary = data.get('itinerary')
        status = data.get('status', 'planned')
        
        # Validate coordinates if provided
        if latitude is not None or longitude is not None:
            is_valid, message = Trip.validate_coordinates(latitude, longitude)
            if not is_valid:
                return jsonify({'error': message}), 400
        
        # Validate budget if provided
        if budget is not None:
            try:
                budget = float(budget)
                if budget < 0:
                    return jsonify({'error': 'Budget must be non-negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Budget must be a valid number'}), 400
        
        # Create trip
        trip_data = {
            'title': title,
            'destination': destination,
            'start_date': start_date,
            'end_date': end_date,
            'user_id': g.current_user.id,
            'latitude': latitude,
            'longitude': longitude,
            'description': description,
            'budget': budget,
            'status': status
        }
        
        if itinerary:
            trip_data['itinerary'] = itinerary
        
        new_trip = Trip(**trip_data)
        
        db.session.add(new_trip)
        db.session.commit()
        
        return jsonify({
            'message': 'Trip created successfully',
            'trip': new_trip.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to create trip',
            'details': str(e)
        }), 500

@trips_bp.route('/<int:trip_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def handle_trip(trip_id):
    current_user = g.current_user  # ✅ Fixed: Use g.current_user
    
    # Get trip
    trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first()
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404
    
    if request.method == 'GET':
        return jsonify({'trip': trip.to_dict()}), 200
    
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields
        for field in ['title', 'destination', 'start_date', 'end_date', 'description', 'budget', 'status', 'latitude', 'longitude', 'itinerary']:
            if field in data:
                setattr(trip, field, data[field])
        
        try:
            db.session.commit()
            return jsonify({
                'message': 'Trip updated successfully',
                'trip': trip.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Update failed: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(trip)
            db.session.commit()
            return jsonify({'message': 'Trip deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@trips_bp.route('/stats', methods=['GET'])
@require_auth
def get_user_trip_stats():
    """Get user's trip statistics."""
    try:
        user_id = g.current_user.id
        
        # Get counts by status
        stats = {
            'total_trips': Trip.query.filter_by(user_id=user_id).count(),
            'planned': Trip.query.filter_by(user_id=user_id, status='planned').count(),
            'active': Trip.query.filter_by(user_id=user_id, status='active').count(),
            'completed': Trip.query.filter_by(user_id=user_id, status='completed').count(),
            'cancelled': Trip.query.filter_by(user_id=user_id, status='cancelled').count(),
        }
        
        # Get total budget
        total_budget = db.session.query(db.func.sum(Trip.budget)).filter(
            Trip.user_id == user_id,
            Trip.budget.isnot(None)
        ).scalar() or 0
        
        stats['total_budget'] = float(total_budget)
        
        # Get upcoming trips
        today = date.today()
        upcoming_trips = Trip.query.filter(
            Trip.user_id == user_id,
            Trip.start_date > today,
            Trip.status.in_(['planned', 'active'])
        ).order_by(Trip.start_date.asc()).limit(5).all()
        
        stats['upcoming_trips'] = [trip.to_dict() for trip in upcoming_trips]
        
        return jsonify({
            'user_id': user_id,
            'stats': stats
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve trip statistics',
            'details': str(e)
        }), 500

@trips_bp.route('/<int:trip_id>/generate-itinerary', methods=['POST'])
@require_auth
def generate_default_itinerary(trip_id):
    """Generate default itinerary for a trip."""
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404
        
        # Check ownership
        if trip.user_id != g.current_user.id and not g.current_user.is_admin:
            return jsonify({'error': 'Unauthorized to modify this trip'}), 403
        
        # Generate default itinerary
        default_itinerary = trip.generate_default_itinerary()
        
        # Option to overwrite existing itinerary
        overwrite = request.json.get('overwrite', False) if request.json else False
        
        if trip.get_itinerary() and not overwrite:
            return jsonify({
                'message': 'Trip already has an itinerary',
                'existing_itinerary': trip.get_itinerary(),
                'suggested_itinerary': default_itinerary,
                'note': 'Send {"overwrite": true} to replace existing itinerary'
            }), 200
        
        # Set the new itinerary
        trip.set_itinerary(default_itinerary)
        trip.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Default itinerary generated successfully',
            'trip_id': trip_id,
            'itinerary': default_itinerary
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to generate itinerary',
            'details': str(e)
        }), 500

@trips_bp.route('/generate-itinerary-preview', methods=['POST'])
@require_auth
def preview_default_itinerary():
    """Preview default itinerary without saving."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['destination', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Generate preview itinerary
        preview_itinerary = ItineraryGenerator.generate_default_itinerary(
            start_date=start_date,
            end_date=end_date,
            destination=data['destination'],
            description=data.get('description', ''),
            title=data.get('title', '')
        )
        
        return jsonify({
            'message': 'Itinerary preview generated',
            'preview_itinerary': preview_itinerary,
            'destination_type': ItineraryGenerator.classify_destination(
                data['destination'], 
                data.get('description', '')
            ),
            'duration_days': (end_date - start_date).days + 1
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Failed to generate itinerary preview',
            'details': str(e)
        }), 500