import requests
import json

BASE_URL = "http://localhost:5000/api"

def get_auth_token():
    """Login and get auth token."""
    login_data = {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()['tokens']['access_token']
    return None

def test_trips_crud():
    """Test all CRUD operations for trips."""
    print("=== Testing Trips CRUD Operations ===\n")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a trip
    print("1. Creating a new trip:")
    trip_data = {
        "title": "Test Trip to Paris",
        "destination": "Paris, France",
        "start_date": "2025-09-01",
        "end_date": "2025-09-07",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "description": "A wonderful test trip to Paris",
        "budget": 2500.00,
        "itinerary": [
            {
                "day": 1,
                "date": "2025-09-01",
                "activities": ["Arrive in Paris", "Check into hotel"]
            },
            {
                "day": 2,
                "date": "2025-09-02",
                "activities": ["Visit Eiffel Tower", "Seine River cruise"]
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/trips/", json=trip_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        trip_id = response.json()['trip']['id']
        print(f"✓ Trip created with ID: {trip_id}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    else:
        print(f"❌ Failed to create trip: {response.json()}")
        return
    
    # 2. Get all trips
    print("2. Getting all trips:")
    response = requests.get(f"{BASE_URL}/trips/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # 3. Get specific trip
    print(f"3. Getting trip with ID {trip_id}:")
    response = requests.get(f"{BASE_URL}/trips/{trip_id}", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # 4. Update trip
    print(f"4. Updating trip with ID {trip_id}:")
    update_data = {
        "title": "Updated Paris Trip",
        "budget": 3000.00,
        "status": "active"
    }
    response = requests.put(f"{BASE_URL}/trips/{trip_id}", json=update_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # 5. Get trip itinerary
    print(f"5. Getting itinerary for trip {trip_id}:")
    response = requests.get(f"{BASE_URL}/trips/{trip_id}/itinerary", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # 6. Update itinerary
    print(f"6. Updating itinerary for trip {trip_id}:")
    itinerary_data = {
        "itinerary": [
            {
                "day": 1,
                "date": "2025-09-01",
                "activities": ["Arrive in Paris", "Check into hotel", "Evening walk"]
            },
            {
                "day": 2,
                "date": "2025-09-02",
                "activities": ["Visit Eiffel Tower", "Seine River cruise", "Dinner at local restaurant"]
            },
            {
                "day": 3,
                "date": "2025-09-03",
                "activities": ["Louvre Museum", "Shopping at Champs-Élysées"]
            }
        ]
    }
    response = requests.put(f"{BASE_URL}/trips/{trip_id}/itinerary", json=itinerary_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # 7. Get user stats
    print("7. Getting user trip statistics:")
    response = requests.get(f"{BASE_URL}/trips/stats", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # 8. Delete trip (optional - uncomment to test)
    # print(f"8. Deleting trip with ID {trip_id}:")
    # response = requests.delete(f"{BASE_URL}/trips/{trip_id}", headers=headers)
    # print(f"Status: {response.status_code}")
    # print(f"Response: {json.dumps(response.json(), indent=2)}\n")

if __name__ == "__main__":
    print("Make sure your Flask app is running...")
    test_trips_crud()