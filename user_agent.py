"""
User agent module for handling user interactions and preferences.
"""

import json
import re
from datetime import datetime
from typing import Dict, List
from models import FlightOption


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
        
        # Default profile (user's information)
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