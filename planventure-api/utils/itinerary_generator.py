from datetime import datetime, timedelta
import re

class ItineraryGenerator:
    """Generate default itinerary templates based on trip details."""
    
    # Destination type keywords for classification
    DESTINATION_KEYWORDS = {
        'beach': ['beach', 'coast', 'island', 'resort', 'tropical', 'bali', 'hawaii', 'maldives', 'caribbean'],
        'city': ['city', 'urban', 'metropolitan', 'downtown', 'paris', 'tokyo', 'london', 'new york', 'berlin'],
        'mountain': ['mountain', 'alpine', 'peak', 'summit', 'hiking', 'trekking', 'alps', 'himalayas'],
        'cultural': ['museum', 'historical', 'heritage', 'temple', 'cathedral', 'palace', 'ancient', 'rome', 'athens'],
        'adventure': ['adventure', 'safari', 'wildlife', 'national park', 'outdoor', 'camping', 'expedition'],
        'business': ['conference', 'business', 'meeting', 'corporate', 'convention', 'trade show'],
        'romantic': ['honeymoon', 'romantic', 'couples', 'anniversary', 'valentine'],
        'family': ['family', 'kids', 'children', 'theme park', 'zoo', 'aquarium', 'disney']
    }
    
    # Activity templates for different destination types
    ACTIVITY_TEMPLATES = {
        'beach': {
            'arrival': ['Arrive at destination', 'Check into beachfront accommodation', 'Welcome drink and resort orientation'],
            'morning': ['Beach relaxation', 'Swimming and sunbathing', 'Water sports activities', 'Beach volleyball'],
            'afternoon': ['Snorkeling or diving', 'Beachside lunch', 'Spa and wellness treatments', 'Local market visit'],
            'evening': ['Sunset viewing', 'Beachside dinner', 'Live music or entertainment', 'Night beach walk'],
            'departure': ['Final beach morning', 'Souvenir shopping', 'Departure preparations', 'Check out and transfer']
        },
        'city': {
            'arrival': ['Arrive in the city', 'Check into hotel', 'Initial city orientation walk'],
            'morning': ['Historic district exploration', 'Famous landmarks tour', 'Museums and galleries', 'Local breakfast spots'],
            'afternoon': ['Shopping districts', 'Cultural sites visit', 'Local cuisine lunch', 'Architectural tours'],
            'evening': ['Dinner at local restaurant', 'Nightlife exploration', 'Theater or entertainment', 'City lights tour'],
            'departure': ['Final city walk', 'Last-minute shopping', 'Coffee at local café', 'Departure to airport']
        },
        'mountain': {
            'arrival': ['Arrive at mountain destination', 'Check into lodge', 'Equipment check and preparation'],
            'morning': ['Hiking and trekking', 'Nature walks', 'Wildlife spotting', 'Photography sessions'],
            'afternoon': ['Mountain climbing', 'Scenic viewpoints', 'Picnic lunch in nature', 'Adventure activities'],
            'evening': ['Campfire and storytelling', 'Stargazing', 'Mountain lodge dinner', 'Rest and recovery'],
            'departure': ['Final morning hike', 'Equipment return', 'Scenic drive back', 'Departure']
        },
        'cultural': {
            'arrival': ['Arrive at cultural destination', 'Check into heritage hotel', 'Initial historical overview'],
            'morning': ['Museums and galleries', 'Historical sites tour', 'Ancient monuments', 'Guided cultural walks'],
            'afternoon': ['Local artisan workshops', 'Traditional performances', 'Heritage buildings', 'Cultural cuisine'],
            'evening': ['Traditional dinner show', 'Local festivals (if available)', 'Cultural center visits', 'Evening prayers/ceremonies'],
            'departure': ['Final museum visit', 'Cultural souvenir shopping', 'Traditional breakfast', 'Departure']
        },
        'adventure': {
            'arrival': ['Arrive at adventure base', 'Equipment briefing', 'Safety orientation'],
            'morning': ['Outdoor adventures', 'Wildlife safari', 'Rock climbing', 'River rafting'],
            'afternoon': ['Extreme sports', 'Nature expeditions', 'Survival training', 'Photography tours'],
            'evening': ['Campfire activities', 'Adventure stories', 'Outdoor dining', 'Night safaris'],
            'departure': ['Final adventure activity', 'Equipment return', 'Group photos', 'Safe departure']
        },
        'business': {
            'arrival': ['Arrive at destination', 'Check into business hotel', 'Conference registration'],
            'morning': ['Business meetings', 'Conference sessions', 'Networking breakfast', 'Keynote presentations'],
            'afternoon': ['Workshops and seminars', 'Business lunches', 'Client meetings', 'Trade show visits'],
            'evening': ['Business dinners', 'Networking events', 'Industry meetups', 'Work preparation'],
            'departure': ['Final meetings', 'Follow-up sessions', 'Business card exchange', 'Departure']
        },
        'romantic': {
            'arrival': ['Romantic arrival', 'Check into romantic suite', 'Welcome champagne'],
            'morning': ['Couples spa treatment', 'Romantic breakfast', 'Private tours', 'Photography session'],
            'afternoon': ['Romantic lunch', 'Couples activities', 'Wine tasting', 'Scenic walks'],
            'evening': ['Candlelit dinner', 'Sunset viewing', 'Dancing', 'Private entertainment'],
            'departure': ['Romantic breakfast', 'Memory collection', 'Final romantic moments', 'Departure']
        },
        'family': {
            'arrival': ['Family arrival', 'Check into family accommodation', 'Family orientation'],
            'morning': ['Family attractions', 'Theme parks', 'Interactive museums', 'Educational tours'],
            'afternoon': ['Family-friendly activities', 'Picnic lunch', 'Playgrounds and parks', 'Family games'],
            'evening': ['Family dinner', 'Entertainment shows', 'Family bonding time', 'Early rest for kids'],
            'departure': ['Final family activity', 'Souvenir shopping for kids', 'Family photos', 'Departure']
        }
    }
    
    @classmethod
    def classify_destination(cls, destination, description=""):
        """
        Classify destination type based on keywords.
        
        Args:
            destination (str): Destination name
            description (str): Trip description
            
        Returns:
            str: Destination type
        """
        text = f"{destination} {description}".lower()
        
        scores = {}
        for dest_type, keywords in cls.DESTINATION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[dest_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return 'city'  # Default to city type
    
    @classmethod
    def generate_daily_activities(cls, day_num, total_days, dest_type, date_str):
        """
        Generate activities for a specific day.
        
        Args:
            day_num (int): Day number (1-based)
            total_days (int): Total trip duration
            dest_type (str): Destination type
            date_str (str): Date string
            
        Returns:
            list: List of activities for the day
        """
        activities = []
        templates = cls.ACTIVITY_TEMPLATES.get(dest_type, cls.ACTIVITY_TEMPLATES['city'])
        
        if day_num == 1:
            # Arrival day
            activities.extend(templates['arrival'][:2])
            if total_days > 1:
                activities.extend(templates['evening'][:1])
        elif day_num == total_days:
            # Departure day
            activities.extend(templates['morning'][:1])
            activities.extend(templates['departure'])
        else:
            # Middle days - full day activities
            activities.extend(templates['morning'][:2])
            activities.extend(templates['afternoon'][:2])
            activities.extend(templates['evening'][:1])
        
        return activities[:4]  # Limit to 4 activities per day
    
    @classmethod
    def get_day_notes(cls, day_num, total_days, dest_type):
        """Generate helpful notes for each day."""
        notes_map = {
            'beach': {
                1: "Apply sunscreen and stay hydrated",
                'middle': "Best time for water activities is morning",
                'last': "Pack souvenirs and enjoy final beach time"
            },
            'city': {
                1: "Comfortable walking shoes recommended",
                'middle': "Book popular attractions in advance",
                'last': "Allow extra time for airport transfer"
            },
            'mountain': {
                1: "Check weather conditions and pack accordingly",
                'middle': "Start early for best views and weather",
                'last': "Ensure all equipment is returned"
            },
            'cultural': {
                1: "Respect local customs and dress codes",
                'middle': "Photography may be restricted in some areas",
                'last': "Visit gift shops for authentic souvenirs"
            },
            'adventure': {
                1: "Safety briefing is mandatory",
                'middle': "Follow all safety guidelines",
                'last': "Share your adventure stories"
            },
            'business': {
                1: "Confirm all meeting times and locations",
                'middle': "Networking opportunities available",
                'last': "Follow up on business connections made"
            },
            'romantic': {
                1: "Special romantic surprise planned",
                'middle': "Perfect day for couples activities",
                'last': "Create lasting memories together"
            },
            'family': {
                1: "Keep kids engaged with family activities",
                'middle': "Balance fun with rest time",
                'last': "Collect family photos and memories"
            }
        }
        
        dest_notes = notes_map.get(dest_type, notes_map['city'])
        
        if day_num == 1:
            return dest_notes.get(1, "Enjoy your first day!")
        elif day_num == total_days:
            return dest_notes.get('last', "Safe travels home!")
        else:
            return dest_notes.get('middle', "Make the most of your day!")
    
    @classmethod
    def generate_default_itinerary(cls, start_date, end_date, destination, description="", title=""):
        """
        Generate a default itinerary template.
        
        Args:
            start_date (date): Trip start date
            end_date (date): Trip end date
            destination (str): Destination name
            description (str): Trip description
            title (str): Trip title
            
        Returns:
            list: Generated itinerary
        """
        try:
            # Calculate duration
            duration = (end_date - start_date).days + 1
            
            # Classify destination type
            dest_type = cls.classify_destination(destination, f"{description} {title}")
            
            # Generate itinerary
            itinerary = []
            current_date = start_date
            
            for day_num in range(1, duration + 1):
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Generate activities for this day
                activities = cls.generate_daily_activities(day_num, duration, dest_type, date_str)
                
                # Add travel tips based on destination type
                notes = cls.get_day_notes(day_num, duration, dest_type)
                
                day_plan = {
                    'day': day_num,
                    'date': date_str,
                    'activities': activities,
                    'notes': notes
                }
                
                itinerary.append(day_plan)
                current_date += timedelta(days=1)
            
            return itinerary
            
        except Exception as e:
            # Return basic itinerary if generation fails
            return cls.generate_basic_itinerary(start_date, end_date)
    
    @classmethod
    def generate_basic_itinerary(cls, start_date, end_date):
        """Generate a basic itinerary as fallback."""
        duration = (end_date - start_date).days + 1
        itinerary = []
        current_date = start_date
        
        for day_num in range(1, duration + 1):
            activities = []
            
            if day_num == 1:
                activities = ["Arrive at destination", "Check into accommodation", "Explore nearby area"]
            elif day_num == duration:
                activities = ["Final sightseeing", "Pack and check out", "Departure"]
            else:
                activities = ["Morning sightseeing", "Lunch at local restaurant", "Afternoon activities", "Evening relaxation"]
            
            itinerary.append({
                'day': day_num,
                'date': current_date.strftime('%Y-%m-%d'),
                'activities': activities,
                'notes': f"Day {day_num} of your trip"
            })
            
            current_date += timedelta(days=1)
        
        return itinerary