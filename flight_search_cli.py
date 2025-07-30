#!/usr/bin/env python3
"""
Natural Language Flight Search CLI
A simple command-line interface for searching flights using natural language queries.
"""

import json
import sys
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import openai
except ImportError:
    print("Error: OpenAI library not installed. Run: pip install openai")
    sys.exit(1)

try:
    from amadeus import Client, ResponseError
except ImportError:
    print("Error: Amadeus library not installed. Run: pip install amadeus")
    sys.exit(1)


@dataclass
class FlightOption:
    """Represents a flight option with analysis data."""
    flight_data: Dict
    price: float
    duration: str
    departure_time: str
    arrival_time: str
    airline: str
    stops: int
    score: float
    recommendation: str


@dataclass
class AgentMessage:
    """Message structure for agent communication."""
    sender: str
    recipient: str
    message_type: str
    content: Any
    timestamp: datetime


class FlightAnalyzer:
    """Analyzes flight options and provides intelligent recommendations."""
    
    def __init__(self):
        self.airline_rankings = {
            'premium': ['SQ', 'LH', 'BA', 'AF', 'CX'],
            'budget': ['AK', 'FR', 'U2', 'WN'],
            'regional': ['TG', 'VN', 'GA']
        }
    
    def analyze_flights(self, flight_data: List[Dict], user_budget: Optional[float] = None) -> List[FlightOption]:
        """Analyze flight options and rank by price (cheapest first)."""
        analyzed_flights = []
        
        for flight in flight_data:
            try:
                option = self._create_flight_option(flight, user_budget)
                analyzed_flights.append(option)
            except Exception as e:
                print(f"Warning: Could not analyze flight: {e}")
                continue
        
        # Sort by price (cheapest first)
        analyzed_flights.sort(key=lambda x: x.price)
        
        return analyzed_flights
    
    def _create_flight_option(self, flight_data: Dict, user_budget: Optional[float]) -> FlightOption:
        """Create a FlightOption from raw flight data."""
        # Extract basic info
        price = float(flight_data.get('price', {}).get('total', 0))
        itineraries = flight_data.get('itineraries', [])
        
        if not itineraries:
            raise ValueError("No itinerary data")
        
        # Analyze first itinerary (outbound)
        segments = itineraries[0].get('segments', [])
        if not segments:
            raise ValueError("No segment data")
        
        # Calculate duration
        duration = itineraries[0].get('duration', 'Unknown')
        
        # Get departure/arrival times
        departure_time = segments[0].get('departure', {}).get('at', '')
        arrival_time = segments[-1].get('arrival', {}).get('at', '')
        
        # Get airline
        airline = segments[0].get('carrierCode', 'Unknown')
        
        # Count stops
        stops = len(segments) - 1
        
        # Generate simple recommendation
        recommendation = self._generate_simple_recommendation(stops, user_budget, price)
        
        return FlightOption(
            flight_data=flight_data,
            price=price,
            duration=duration,
            departure_time=departure_time,
            arrival_time=arrival_time,
            airline=airline,
            stops=stops,
            score=0,  # Not used anymore
            recommendation=recommendation
        )
    
    def _generate_simple_recommendation(self, stops: int, user_budget: Optional[float], price: float) -> str:
        """Generate a simple recommendation based on stops and budget."""
        recommendations = []
        
        # Stop information
        if stops == 0:
            recommendations.append("Direct flight")
        elif stops == 1:
            recommendations.append("1 stop")
        else:
            recommendations.append(f"{stops} stops")
        
        # Budget comparison
        if user_budget:
            if price <= user_budget * 0.8:
                recommendations.append("Great value")
            elif price <= user_budget:
                recommendations.append("Within budget")
            else:
                recommendations.append("Over budget")
        
        return " • ".join(recommendations)


class UserAgent:
    """Handles user interaction and represents user preferences."""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.preferences = {}
        self.conversation_history = []
    
    def parse_initial_request(self, user_query: str) -> Dict:
        """Parse user's initial flight request."""
        # Enhanced parsing with budget extraction
        today = datetime.now()
        current_year = today.year
        
        prompt = f"""
Parse this flight search request and extract budget information: "{user_query}"

Current date: {today.strftime('%Y-%m-%d')}

Extract these parameters (set to null if not mentioned):
- origin: IATA airport code (3 letters)
- destination: IATA airport code (3 letters) 
- departure_date: Date in YYYY-MM-DD format (use {current_year} as year)
- return_date: Return date if mentioned
- adults: Number of adults (default 1)
- children: Number of children
- infants: Number of infants
- budget: Extract budget amount as number (from phrases like "budget $400", "under $500", "max 300")
- currency: Currency code (USD, EUR, SGD, etc.)
- non_stop: true if "direct" or "non-stop" mentioned
- preferred_airlines: Array of airline codes if mentioned
- avoided_airlines: Array of airline codes to avoid

IATA mappings:
- KUL = Kuala Lumpur, Malaysia
- BKK = Bangkok, Thailand  
- SIN = Singapore
- NYC = JFK or LGA (New York)

Budget extraction examples:
- "budget is $400" → budget: 400, currency: "USD"
- "under $500" → budget: 500, currency: "USD"
- "max 300 euros" → budget: 300, currency: "EUR"

Respond with JSON only:
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract flight search parameters from user queries. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0
            )
            
            content = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(content)
                
        except Exception as e:
            raise ValueError(f"Could not parse user request: {e}")
    
    def present_options(self, flight_options: List[FlightOption]) -> str:
        """Present flight options to user in a conversational way."""
        if not flight_options:
            return "I couldn't find any flights matching your criteria. Would you like to try different dates or destinations?"
        
        # Take top 3 options
        top_options = flight_options[:3]
        
        presentation = f"🛫 I found {len(flight_options)} flights! Here are the top 3 options:\n\n"
        
        for i, option in enumerate(top_options, 1):
            presentation += f"{i}. {option.airline} - ${option.price:.0f}\n"
            presentation += f"   ⏰ {option.departure_time[:10]} {option.departure_time[11:16]} → {option.arrival_time[11:16]}\n"
            presentation += f"   ✈️ {option.recommendation}\n\n"
        
        presentation += "Which option would you like me to book? (1, 2, 3, or 'show more' for other options)"
        return presentation
    
    def collect_traveler_info(self, num_adults: int = 1, num_children: int = 0, num_infants: int = 0) -> List[Dict]:
        """Collect traveler information for booking with auto-fill capability."""
        travelers = []
        
        # Default profile (your information)
        default_profile = {
            "first_name": "BRIAN",
            "last_name": "HAR", 
            "date_of_birth": "2003-05-20",
            "gender": "MALE",
            "email": "sze@gmail.com",
            "country_code": "60",
            "phone": "0149942098",
            "passport_number": "ACB821909",
            "passport_expiry": "2026-09-10",
            "passport_issue": "2021-09-10",
            "passport_country": "MY",
            "birth_place": "Johor"
        }
        
        # Collect adult travelers
        for i in range(num_adults):
            print(f"\n=== Adult Traveler {i+1} ===")
            
            # Ask if user wants to use auto-fill
            use_autofill = input("Use auto-fill with saved profile? (y/n): ").strip().lower()
            
            if use_autofill == 'y':
                print("✅ Using auto-fill...")
                first_name = default_profile["first_name"]
                last_name = default_profile["last_name"]
                date_of_birth = default_profile["date_of_birth"]
                gender = default_profile["gender"]
                email = default_profile["email"]
                country_code = default_profile["country_code"]
                phone = default_profile["phone"]
                passport_number = default_profile["passport_number"]
                passport_expiry = default_profile["passport_expiry"]
                passport_issue = default_profile["passport_issue"]
                passport_country = default_profile["passport_country"]
                birth_place = default_profile["birth_place"]
                
                # Show filled values
                print(f"Name: {first_name} {last_name}")
                print(f"DOB: {date_of_birth}")
                print(f"Email: {email}")
                print(f"Passport: {passport_number}")
                
            else:
                # Manual input
                first_name = input("First name: ").strip().upper()
                last_name = input("Last name: ").strip().upper()
                date_of_birth = input("Date of birth (YYYY-MM-DD): ").strip()
                gender = input("Gender (MALE/FEMALE): ").strip().upper()
                email = input("Email: ").strip()
                country_code = input("Country code (e.g., 60): ").strip()
                phone = input("Phone number: ").strip()
                passport_number = input("Passport number: ").strip()
                passport_expiry = input("Passport expiry (YYYY-MM-DD): ").strip()
                passport_issue = input("Passport issue date (YYYY-MM-DD): ").strip()
                passport_country = input("Passport country (2-letter code, e.g., MY): ").strip().upper()
                birth_place = input("Birth place (city): ").strip()
            
            # Create traveler object with complete Amadeus format
            traveler = {
                "id": str(i + 1),
                "dateOfBirth": date_of_birth,
                "name": {
                    "firstName": first_name,
                    "lastName": last_name
                },
                "gender": gender,
                "contact": {
                    "emailAddress": email,
                    "phones": [{
                        "deviceType": "MOBILE",
                        "countryCallingCode": country_code,
                        "number": phone
                    }]
                },
                "documents": [{
                    "documentType": "PASSPORT",
                    "birthPlace": birth_place,
                    "issuanceLocation": birth_place,
                    "issuanceDate": passport_issue,
                    "number": passport_number,
                    "expiryDate": passport_expiry,
                    "issuanceCountry": passport_country,
                    "validityCountry": passport_country,
                    "nationality": passport_country,
                    "holder": True
                }]
            }
            travelers.append(traveler)
        
        return travelers
    
    def collect_booking_contact(self) -> Dict:
        """Collect contact information for booking with auto-fill."""
        print("\n=== Booking Contact Information ===")
        print("(This can be different from traveler contact)")
        
        # Ask if user wants to use auto-fill
        use_autofill = input("Use auto-fill for contact info? (y/n): ").strip().lower()
        
        if use_autofill == 'y':
            print("✅ Using auto-fill for contact...")
            first_name = "BRIAN"
            last_name = "HAR"
            email = "sze@gmail.com"
            country_code = "60"
            phone = "0149942098"
            
            print(f"Contact: {first_name} {last_name}")
            print(f"Email: {email}")
            
        else:
            first_name = input("Contact first name: ").strip().upper()
            last_name = input("Contact last name: ").strip().upper()
            email = input("Contact email: ").strip()
            country_code = input("Country code (e.g., 60): ").strip()
            phone = input("Phone number: ").strip()
        
        return {
            "addresseeName": {
                "firstName": first_name,
                "lastName": last_name
            },
            "companyName": "TRAVEL BOOKING",
            "purpose": "STANDARD",
            "phones": [{
                "deviceType": "MOBILE",
                "countryCallingCode": country_code,
                "number": phone
            }],
            "emailAddress": email,
            "address": {
                "lines": ["Online Booking"],
                "postalCode": "00000",
                "cityName": "Online",
                "countryCode": "MY"
            }
        }


class TravelAgent:
    """Handles flight search, analysis, and booking operations."""
    
    def __init__(self, amadeus_client, openai_client):
        self.amadeus_client = amadeus_client
        self.openai_client = openai_client
        self.flight_analyzer = FlightAnalyzer()
        self.message_queue = []
    
    def search_and_analyze(self, search_params: Dict) -> List[FlightOption]:
        """Search for flights and analyze options."""
        try:
            # Build search parameters
            api_params = {
                'originLocationCode': search_params['origin'],
                'destinationLocationCode': search_params['destination'],
                'departureDate': search_params['departure_date'],
                'adults': search_params.get('adults', 1)
            }
            
            # Add optional parameters
            if search_params.get('return_date'):
                api_params['returnDate'] = search_params['return_date']
            if search_params.get('children'):
                api_params['children'] = search_params['children']
            if search_params.get('infants'):
                api_params['infants'] = search_params['infants']
            if search_params.get('non_stop'):
                api_params['nonStop'] = 'true'
            if search_params.get('currency'):
                api_params['currencyCode'] = search_params['currency']
            
            # Search flights
            print("🔍 Searching for flights...")
            response = self.amadeus_client.shopping.flight_offers_search.get(**api_params)
            
            print(f"✅ Found {len(response.data)} flight options")
            
            # Analyze flights
            print("🤖 Analyzing options...")
            analyzed_options = self.flight_analyzer.analyze_flights(
                response.data, 
                search_params.get('budget')
            )
            
            return analyzed_options
            
        except ResponseError as e:
            raise ValueError(f"Flight search failed: {e.description}")
        except Exception as e:
            raise ValueError(f"Unexpected error during search: {e}")
    
    def book_flight(self, flight_option: FlightOption, travelers: List[Dict], contact: Dict) -> Dict:
        """Book the selected flight with complete API format."""
        try:
            print("📋 Processing booking...")
            
            # Step 1: Refresh flight data to avoid schedule changes
            print("🔄 Validating flight availability...")
            validated_flight = self._validate_flight_pricing(flight_option.flight_data)
            
            # Step 2: Fix traveler IDs to match flight offer pricing
            corrected_travelers = self._match_traveler_ids(validated_flight, travelers)
            
            # Prepare the complete booking request body
            booking_body = {
                "data": {
                    "type": "flight-order",
                    "flightOffers": [validated_flight],
                    "travelers": corrected_travelers,
                    "remarks": {
                        "general": [{
                            "subType": "GENERAL_MISCELLANEOUS",
                            "text": "ONLINE BOOKING FROM AUTONOMOUS AGENT"
                        }]
                    },
                    "ticketingAgreement": {
                        "option": "DELAY_TO_CANCEL",
                        "delay": "6D"
                    },
                    "contacts": [contact]
                }
            }
            
            print("🔍 Debug - Sending booking request...")
            print(f"🔍 Debug - Flight offer ID: {flight_option.flight_data.get('id', 'No ID')}")
            print(f"🔍 Debug - Original travelers: {len(travelers)}")
            print(f"🔍 Debug - Corrected travelers: {len(corrected_travelers)}")
            print(f"🔍 Debug - Traveler IDs: {[t['id'] for t in corrected_travelers]}")
            
            # Make booking using raw POST request (more control over format)
            response = self.amadeus_client.post('/v1/booking/flight-orders', booking_body)
            
            print("✅ Booking successful!")
            return response.data
            
        except ResponseError as e:
            # Better error handling
            print(f"🔍 Debug - Response status: {e.response.status_code}")
            print(f"🔍 Debug - Response body: {e.response.body}")
            
            # Try to parse the error details
            try:
                error_body = json.loads(e.response.body) if e.response.body else {}
                if 'errors' in error_body:
                    for error in error_body['errors']:
                        print(f"❌ API Error: {error.get('detail', 'Unknown error')}")
                        if 'source' in error:
                            print(f"   Field: {error['source'].get('parameter', 'Unknown field')}")
            except:
                pass
                
            raise ValueError(f"Booking failed: {e.description} (Status: {e.response.status_code})")
        except Exception as e:
            print(f"🔍 Debug - Exception type: {type(e)}")
            print(f"🔍 Debug - Exception: {str(e)}")
            raise ValueError(f"Unexpected booking error: {e}")
    
    def _match_traveler_ids(self, flight_offer: Dict, travelers: List[Dict]) -> List[Dict]:
        """Match traveler IDs to those expected in the flight offer."""
        try:
            # Extract traveler pricings from flight offer
            traveler_pricings = flight_offer.get('travelerPricings', [])
            
            if not traveler_pricings:
                print("⚠️ Warning: No traveler pricings found in flight offer")
                return travelers
            
            # Create corrected travelers list
            corrected_travelers = []
            
            for i, pricing in enumerate(traveler_pricings):
                expected_id = pricing.get('travelerId', str(i + 1))
                
                if i < len(travelers):
                    # Update existing traveler with correct ID
                    traveler = travelers[i].copy()
                    traveler['id'] = expected_id
                    corrected_travelers.append(traveler)
                else:
                    print(f"⚠️ Warning: Not enough travelers provided for travelerId {expected_id}")
            
            print(f"🔍 Debug - Expected traveler IDs from offer: {[p.get('travelerId') for p in traveler_pricings]}")
            print(f"🔍 Debug - Assigned traveler IDs: {[t['id'] for t in corrected_travelers]}")
            
            return corrected_travelers
            
        except Exception as e:
            print(f"⚠️ Warning: Could not match traveler IDs: {e}")
            return travelers
    
    def _validate_flight_pricing(self, flight_data: Dict) -> Dict:
        """Validate flight pricing to get fresh schedule data using proper API format."""
        try:
            # Prepare pricing request with correct format
            pricing_body = {
                "data": {
                    "type": "flight-offers-pricing",
                    "flightOffers": [flight_data]
                }
            }
            
            # Call pricing API using raw POST to ensure correct format
            response = self.amadeus_client.post('/v1/shopping/flight-offers/pricing', pricing_body)
            
            if response.data and 'flightOffers' in response.data and len(response.data['flightOffers']) > 0:
                print("✅ Flight validated with current schedule")
                return response.data['flightOffers'][0]  # Return the refreshed flight data
            else:
                print("⚠️ No pricing data returned, using original flight")
                return flight_data
                
        except ResponseError as e:
            print(f"⚠️ Could not validate pricing: {e.description}")
            print("🔄 Using original flight data")
            return flight_data
        except Exception as e:
            print(f"⚠️ Pricing validation error: {e}")
            return flight_data


class FlightSearchCLI:
    def __init__(self):
        # Hardcoded credentials for development
        self.amadeus_client_id = 'YOUR_CLIENT_ID'  # Replace with your Amadeus client ID
        self.amadeus_client_secret = 'YOUR_CLIENT_SECRET'  # Replace with your Amadeus client secret
        self.openai_api_key = 'sk-proj-xxx'  # Replace with your OpenAI API key
        
        self.amadeus_client = None
        self.openai_client = None
        
        # Multi-Agent System
        self.user_agent = None
        self.travel_agent = None
        
        # Current session data
        self.current_search_params = None
        self.current_flight_options = None
        self.selected_flight = None
    
    def initialize_clients(self):
        """Initialize Amadeus, OpenAI clients and agents."""
        try:
            # Initialize Amadeus client
            self.amadeus_client = Client(
                client_id=self.amadeus_client_id,
                client_secret=self.amadeus_client_secret
            )
            
            # Initialize OpenAI client
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            
            # Initialize agents
            self.user_agent = UserAgent(self.openai_client)
            self.travel_agent = TravelAgent(self.amadeus_client, self.openai_client)
            
            print("✓ API clients and agents initialized successfully")
            
        except Exception as e:
            print(f"Error initializing clients: {e}")
            sys.exit(1)
    
    def parse_natural_language_query(self, query):
        """Use OpenAI to extract flight search parameters from natural language."""
        try:
            # Get current date for reference
            today = datetime.now()
            current_year = today.year
            
            prompt = f"""
Extract flight search parameters from this natural language query: "{query}"

Current date: {today.strftime('%Y-%m-%d')}
Current year: {current_year}

Please respond with a JSON object containing these fields (set to null if not mentioned):

REQUIRED:
- origin: IATA airport code (3 letters, e.g., "SYD")
- destination: IATA airport code (3 letters, e.g., "BKK")
- departure_date: Date in YYYY-MM-DD format (use {current_year} as the year unless specified otherwise)
- adults: Number of adult passengers (integer, default 1 if not specified)

OPTIONAL:
- return_date: Return date in YYYY-MM-DD format (for round-trip flights)
- children: Number of children (integer, ages 2-11)
- infants: Number of infants (integer, under 2 years old)
- included_airline_codes: Array of IATA airline codes to include (e.g., ["BA", "LH"])
- excluded_airline_codes: Array of IATA airline codes to exclude (e.g., ["FR", "U2"])
- non_stop: Boolean (true for direct flights only, false or null otherwise)
- currency_code: ISO 4217 currency code (e.g., "USD", "EUR", "SGD")
- max_price: Maximum price limit (number)
- max_results: Maximum number of results to return (integer, >1)

Important IATA code mappings:
- SG, Singapore = SIN
- MY, Malaysia = KUL (Kuala Lumpur)
- MYR (currency) likely means Malaysia = KUL
- NYC, New York = JFK or LGA
- London = LHR
- Tokyo = NRT or HND

Common airline codes:
- BA = British Airways, LH = Lufthansa, AF = Air France
- AA = American Airlines, UA = United Airlines, DL = Delta
- SQ = Singapore Airlines, TG = Thai Airways, CX = Cathay Pacific

Currency detection:
- "dollars", "USD" = USD
- "euros", "EUR" = EUR  
- "pounds", "GBP" = GBP
- "singapore dollars", "SGD" = SGD

Keywords for features:
- "direct", "non-stop", "no connections" = non_stop: true
- "round trip", "return" = include return_date
- "children", "kids" = children count
- "babies", "infants" = infants count
- "under $500", "max $300" = max_price
- "avoid [airline]", "not [airline]" = excluded_airline_codes
- "prefer [airline]", "only [airline]" = included_airline_codes

Example response:
{{
    "origin": "SYD",
    "destination": "BKK",
    "departure_date": "{current_year}-07-15",
    "return_date": "{current_year}-07-22",
    "adults": 2,
    "children": 1,
    "infants": null,
    "included_airline_codes": ["TG", "SQ"],
    "excluded_airline_codes": null,
    "non_stop": true,
    "currency_code": "USD",
    "max_price": 500,
    "max_results": 10
}}

Query: "{query}"
Response:
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts flight search parameters from natural language queries. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parameters = json.loads(json_str)
            else:
                parameters = json.loads(content)
            
            # Validate required parameters
            if not parameters.get('origin') or not parameters.get('destination'):
                raise ValueError("Could not extract origin and destination from query")
            
            # Set default departure date if not provided
            if not parameters.get('departure_date'):
                default_date = datetime.now() + timedelta(days=7)
                parameters['departure_date'] = default_date.strftime('%Y-%m-%d')
            
            # Validate and fix date format if needed
            departure_date = parameters.get('departure_date')
            if departure_date:
                try:
                    # Parse the date to ensure it's valid
                    parsed_date = datetime.strptime(departure_date, '%Y-%m-%d')
                    # If the year is in the past, update it to current year
                    if parsed_date.year < datetime.now().year:
                        parsed_date = parsed_date.replace(year=datetime.now().year)
                        parameters['departure_date'] = parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    # If date parsing fails, use default
                    default_date = datetime.now() + timedelta(days=7)
                    parameters['departure_date'] = default_date.strftime('%Y-%m-%d')
            
            # Set default adults if not provided
            if not parameters.get('adults'):
                parameters['adults'] = 1
                
            return parameters
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing natural language query: {e}")
    
    # Search for flights using Amadeus API with dynamic parameters
    # now AI can handle more complex queries with optional parameters - search for flights using Amadeus API
    def search_flights(self, parameters):
        """Search for flights using Amadeus API with dynamic parameters."""
        try:
            # Build API parameters dynamically
            api_params = {
                'originLocationCode': parameters['origin'],
                'destinationLocationCode': parameters['destination'],
                'departureDate': parameters['departure_date'],
                'adults': parameters['adults']
            }
            
            # Add optional parameters if they exist and are not null
            if parameters.get('return_date'):
                api_params['returnDate'] = parameters['return_date']
            
            if parameters.get('children') and parameters['children'] > 0:
                api_params['children'] = parameters['children']
                
            if parameters.get('infants') and parameters['infants'] > 0:
                api_params['infants'] = parameters['infants']
                
            if parameters.get('included_airline_codes'):
                # Convert array to comma-separated string
                api_params['includedAirlineCodes'] = ','.join(parameters['included_airline_codes'])
                
            if parameters.get('excluded_airline_codes'):
                # Convert array to comma-separated string  
                api_params['excludedAirlineCodes'] = ','.join(parameters['excluded_airline_codes'])
                
            if parameters.get('non_stop') is True:
                api_params['nonStop'] = 'true'
            elif parameters.get('non_stop') is False:
                api_params['nonStop'] = 'false'
                
            if parameters.get('currency_code'):
                api_params['currencyCode'] = parameters['currency_code']
                
            if parameters.get('max_price') and parameters['max_price'] > 0:
                api_params['maxPrice'] = parameters['max_price']
                
            if parameters.get('max_results') and parameters['max_results'] > 1:
                api_params['max'] = parameters['max_results']
            
            # Make the API call with all parameters
            response = self.amadeus_client.shopping.flight_offers_search.get(**api_params)
            
            return response.data
            
        except ResponseError as e:
            if e.response.status_code == 400:
                raise ValueError(f"Invalid search parameters: {e.description}")
            elif e.response.status_code == 401:
                raise ValueError("Authentication failed. Please check your Amadeus credentials.")
            elif e.response.status_code == 500:
                raise ValueError("Amadeus API server error. Please try again later.")
            else:
                raise ValueError(f"API error: {e.description}")
        except Exception as e:
            raise ValueError(f"Unexpected error during flight search: {e}")
    
    def format_output(self, data):
        """Format the flight data as JSON."""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def run_autonomous_agent(self):
        """Main autonomous agent workflow: Search → Compare → Book."""
        try:
            print("=== 🤖 Autonomous Flight Booking Agent ===")
            print("I'm your travel agent. I'll search, analyze, and book flights for you!\n")
            
            # Initialize clients and agents
            self.initialize_clients()
            
            print("\n=== ✈️ Flight Booking Service ===")
            print("Example: 'Find me the best flights from KUL to BKK, direct flight, budget $400'")
            print("Type 'quit' to exit.\n")
            
            while True:
                try:
                    # Get user request
                    user_query = input("🗣️ What flight do you need? ").strip()
                    
                    if user_query.lower() in ['quit', 'exit', 'q']:
                        print("✈️ Thank you for using our booking service. Safe travels!")
                        break
                    
                    if not user_query:
                        print("Please tell me what flight you're looking for.")
                        continue
                    
                    # Agent workflow
                    success = self.execute_agent_workflow(user_query)
                    
                    if success:
                        print("\n🎉 Booking completed! Have a great trip!")
                    else:
                        print("\n💔 Booking not completed. Feel free to try another search!")
                    
                    print("\n" + "="*60 + "\n")
                    
                except KeyboardInterrupt:
                    print("\nType 'quit' to exit.")
                    continue
                except Exception as e:
                    print(f"❌ Unexpected error: {e}")
                    print("Let's try again.\n")
                    continue
                    
        except KeyboardInterrupt:
            print("\n✈️ Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)
    
    def execute_agent_workflow(self, user_query: str) -> bool:
        """Execute the autonomous agent workflow."""
        try:
            # Phase 1: User Agent parses request
            print("\n🧠 User Agent: Understanding your request...")
            search_params = self.user_agent.parse_initial_request(user_query)
            print(f"✓ Understood: {search_params['origin']} → {search_params['destination']}")
            if search_params.get('budget'):
                print(f"💰 Budget: ${search_params['budget']} {search_params.get('currency', 'USD')}")
            
            self.current_search_params = search_params
            
            # Phase 2: Travel Agent searches and analyzes
            print("\n🔍 Travel Agent: Searching and analyzing flights...")
            flight_options = self.travel_agent.search_and_analyze(search_params)
            
            if not flight_options:
                print("❌ No flights found matching your criteria.")
                return False
            
            self.current_flight_options = flight_options
            
            # Export flight data to JSON file with timestamp
            self.export_flight_data(search_params, flight_options)
            
            # Phase 3: User Agent presents options
            print("\n📋 User Agent: Here are the best options I found:")
            presentation = self.user_agent.present_options(flight_options)
            print(presentation)
            
            # Phase 4: Get user confirmation
            while True:
                choice = input("\n🤔 Your choice: ").strip().lower()
                
                if choice in ['1', '2', '3']:
                    option_index = int(choice) - 1
                    if option_index < len(flight_options):
                        self.selected_flight = flight_options[option_index]
                        break
                    else:
                        print("Invalid option. Please choose 1, 2, or 3.")
                elif choice in ['no', 'n', 'cancel']:
                    print("🚫 Booking cancelled.")
                    return False
                elif choice == 'show more':
                    # Show more options
                    if len(flight_options) > 3:
                        print("\n📋 Additional options:")
                        for i, option in enumerate(flight_options[3:6], 4):
                            print(f"{i}. {option.airline} - ${option.price:.0f} • {option.recommendation}")
                    else:
                        print("No more options available.")
                    continue
                else:
                    print("Please enter 1, 2, 3, 'show more', or 'no' to cancel.")
                    continue
            
            # Phase 5: Collect traveler information
            print(f"\n👤 Great choice! {self.selected_flight.airline} for ${self.selected_flight.price:.0f}")
            print("Now I need some traveler information for the booking...")
            
            num_adults = search_params.get('adults', 1)
            num_children = search_params.get('children', 0)
            num_infants = search_params.get('infants', 0)
            
            travelers = self.user_agent.collect_traveler_info(num_adults, num_children, num_infants)
            
            # Phase 5.5: Collect booking contact
            contact = self.user_agent.collect_booking_contact()
            
            # Phase 6: Travel Agent executes booking with auto-retry
            print("\n💳 Travel Agent: Processing your booking...")
            booking_result = self.attempt_booking_with_retry(travelers, contact)
            
            # Phase 7: Confirmation
            print(f"\n🎫 Booking Confirmation:")
            print(f"PNR: {booking_result.get('id', 'N/A')}")
            print(f"Flight: {self.selected_flight.airline}")
            print(f"Route: {search_params['origin']} → {search_params['destination']}")
            print(f"Price: ${self.selected_flight.price:.0f}")
            
            return True
            
        except ValueError as e:
            print(f"❌ {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error in workflow: {e}")
            return False
    
    def attempt_booking_with_retry(self, travelers: List[Dict], contact: Dict, max_retries: int = 2) -> Dict:
        """Attempt booking with automatic re-search on schedule change errors."""
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"\n🔄 Retry attempt {attempt}/{max_retries}...")
                
                # Try booking with current flight selection
                booking_result = self.travel_agent.book_flight(self.selected_flight, travelers, contact)
                return booking_result
                
            except ValueError as e:
                error_msg = str(e).lower()
                
                # Check if it's a schedule change error
                if "schedule change" in error_msg or "segment sell failure" in error_msg:
                    print(f"\n⏰ Flight schedule changed! Auto-searching for updated flights...")
                    
                    if attempt < max_retries:
                        # Re-search for flights with same parameters
                        try:
                            print("🔍 Getting fresh flight data...")
                            fresh_options = self.travel_agent.search_and_analyze(self.current_search_params)
                            
                            if fresh_options:
                                # Find similar flight (same airline/time if possible)
                                new_selection = self.find_similar_flight(fresh_options, self.selected_flight)
                                
                                if new_selection:
                                    self.selected_flight = new_selection
                                    print(f"✅ Found updated flight: {new_selection.airline} - ${new_selection.price:.0f}")
                                    print(f"   New time: {new_selection.departure_time[11:16]}")
                                    continue  # Try booking again
                                else:
                                    print("❌ Could not find similar flight in updated results")
                                    break
                            else:
                                print("❌ No flights available in fresh search")
                                break
                                
                        except Exception as search_error:
                            print(f"❌ Error during re-search: {search_error}")
                            break
                    else:
                        print(f"❌ Max retries ({max_retries}) reached")
                        break
                else:
                    # Different error, don't retry
                    raise e
        
        # If we get here, all retries failed
        raise ValueError("Booking failed after automatic retries due to schedule changes")
    
    def find_similar_flight(self, fresh_options: List, original_flight) -> Optional[FlightOption]:
        """Find a similar flight in fresh search results."""
        try:
            # First, try to find exact same airline and similar time
            original_time = original_flight.departure_time[11:16]  # HH:MM format
            original_airline = original_flight.airline
            
            for option in fresh_options:
                # Same airline
                if option.airline == original_airline:
                    # Check if departure time is within 2 hours
                    option_time = option.departure_time[11:16]
                    
                    # Simple time comparison (you could make this more sophisticated)
                    original_minutes = int(original_time[:2]) * 60 + int(original_time[3:])
                    option_minutes = int(option_time[:2]) * 60 + int(option_time[3:])
                    
                    if abs(original_minutes - option_minutes) <= 120:  # Within 2 hours
                        return option
            
            # If no similar airline/time, just return the cheapest option
            print("⚠️ Could not find similar flight, selecting cheapest available")
            return fresh_options[0] if fresh_options else None
            
        except Exception as e:
            print(f"⚠️ Error finding similar flight: {e}")
            return fresh_options[0] if fresh_options else None
    
    def export_flight_data(self, search_params: Dict, flight_options: List[FlightOption]):
        """Export flight search results to timestamped JSON file."""
        try:
            from datetime import datetime
            
            # Create timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flight_search_{timestamp}.json"
            
            # Prepare export data
            export_data = {
                "search_timestamp": datetime.now().isoformat(),
                "search_parameters": search_params,
                "total_flights_found": len(flight_options),
                "flight_analysis": []
            }
            
            # Add analyzed flight data
            for i, option in enumerate(flight_options):
                flight_analysis = {
                    "rank": i + 1,
                    "airline_code": option.airline,
                    "price": option.price,
                    "currency": search_params.get('currency', 'USD'),
                    "departure_time": option.departure_time,
                    "arrival_time": option.arrival_time,
                    "duration": option.duration,
                    "stops": option.stops,
                    "recommendation": option.recommendation,
                    "raw_flight_data": option.flight_data
                }
                export_data["flight_analysis"].append(flight_analysis)
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📁 Flight data exported to: {filename}")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not export flight data: {e}")
            # Don't fail the booking process if export fails


if __name__ == "__main__":
    cli = FlightSearchCLI()
    cli.run_autonomous_agent()