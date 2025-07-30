#!/usr/bin/env python3
"""
Autonomous Flight Booking Agent - Main CLI
A modular autonomous agent for searching and booking flights using natural language.
"""

import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# External dependencies
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

# Internal modules
from models import FlightOption
from user_agent import UserAgent
from travel_agent import TravelAgent

class FlightBookingAgent:
    """Main autonomous flight booking agent with modular architecture."""
    
    def __init__(self):
        # hardcoded credentials for dev (I didn't set up .env for ease of testing)
        self.amadeus_client_id = 'YOUR_CLIENT_ID'  # Replace with your Amadeus client ID
        self.amadeus_client_secret = 'YOUR_CLIENT_SECRET'  # Replace with your Amadeus client secret
        self.openai_api_key = 'YOUR_KEY_HERE'  # Replace with your OpenAI API key
        
        # API clients
        self.amadeus_client = None
        self.openai_client = None
        
        # Agent modules
        self.user_agent = None
        self.travel_agent = None
        
        # Session data
        self.current_search_params = None
        self.current_flight_options = None
        self.selected_flight = None

    def initialize_clients(self):
        """Initialize API clients and agent modules."""
        try:
            # Initialize API clients
            self.amadeus_client = Client(
                client_id=self.amadeus_client_id,
                client_secret=self.amadeus_client_secret
            )
            
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            
            # Initialize agent modules
            self.user_agent = UserAgent(self.openai_client)
            self.travel_agent = TravelAgent(self.amadeus_client, self.openai_client)
            
            print("✓ API clients and agents initialized successfully")
            
        except Exception as e:
            print(f"Error initializing clients: {e}")
            sys.exit(1)

    def run_autonomous_agent(self):
        """Main autonomous agent workflow: Search → Compare → Book."""
        try:
            print("=== 🤖 Autonomous Flight Booking Agent ===")
            print("I'm your travel agent. I'll search, analyze, and book flights for you!\n")
            
            # Initialize clients and agents
            self.initialize_clients()
            
            print("\n=== ✈️ Flight Booking Service ===")
            print("Example: 'Find me the best flights from KUL to BKK, direct flight, budget $400'")
            print("Or type 'check [flight-order-id]' to verify an existing booking")
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
                    
                    # Check if user wants to verify an existing booking
                    if user_query.lower().startswith('check '):
                        flight_order_id = user_query[6:].strip()
                        if flight_order_id:
                            success = self.check_booking(flight_order_id)
                        else:
                            print("Please provide a flight order ID. Example: 'check eJzTd9c3N3b2C%2FUCAApkAkA%3D'")
                            continue
                    else:
                        # Execute agent workflow
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

    def check_booking(self, flight_order_id: str) -> bool:
        """Check booking details using flight order ID."""
        try:
            print(f"\n🔍 Checking booking: {flight_order_id}")
            
            # Get booking details from travel agent
            booking_details = self.travel_agent.get_booking_details(flight_order_id)
            
            # Display booking information
            print(f"\n📋 Booking Details:")
            
            # Basic booking info
            if 'id' in booking_details:
                print(f"Flight Order ID: {booking_details['id']}")
            
            if 'associatedRecords' in booking_details and booking_details['associatedRecords']:
                record = booking_details['associatedRecords'][0]
                if 'reference' in record:
                    print(f"PNR Reference: {record['reference']}")
                if 'creationDate' in record:
                    print(f"Booking Date: {record['creationDate'][:10]}")
            
            # Flight information
            if 'flightOffers' in booking_details and booking_details['flightOffers']:
                flight_offer = booking_details['flightOffers'][0]
                
                if 'price' in flight_offer:
                    print(f"Total Price: {flight_offer['price'].get('currency', 'USD')} {flight_offer['price'].get('total', 'N/A')}")
                
                if 'itineraries' in flight_offer:
                    for i, itinerary in enumerate(flight_offer['itineraries']):
                        print(f"\n✈️ Flight {i+1}:")
                        if 'segments' in itinerary:
                            for j, segment in enumerate(itinerary['segments']):
                                departure = segment.get('departure', {})
                                arrival = segment.get('arrival', {})
                                print(f"  Segment {j+1}: {departure.get('iataCode', 'N/A')} → {arrival.get('iataCode', 'N/A')}")
                                print(f"  Departure: {departure.get('at', 'N/A')}")
                                print(f"  Arrival: {arrival.get('at', 'N/A')}")
                                print(f"  Airline: {segment.get('carrierCode', 'N/A')}")
            
            # Traveler information
            if 'travelers' in booking_details:
                print(f"\n👥 Travelers ({len(booking_details['travelers'])}):")
                for i, traveler in enumerate(booking_details['travelers'], 1):
                    if 'name' in traveler:
                        name = traveler['name']
                        print(f"  {i}. {name.get('firstName', '')} {name.get('lastName', '')}")
            
            print(f"\n✅ Booking verification complete!")
            return True
            
        except ValueError as e:
            print(f"❌ {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error checking booking: {e}")
            return False

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
            
            # Export flight data to JSON file
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
            
            # Phase 6: Travel Agent executes booking
            print("\n💳 Travel Agent: Processing your booking...")
            booking_result = self.attempt_booking_with_retry(travelers, contact)
            
            # Phase 7: Confirmation
            flight_order_id = booking_result.get('id', 'N/A')
            print(f"\n🎫 Booking Confirmation:")
            print(f"PNR: {flight_order_id}")
            print(f"Flight: {self.selected_flight.airline}")
            print(f"Route: {search_params['origin']} → {search_params['destination']}")
            print(f"Price: ${self.selected_flight.price:.0f}")
            
            # Provide verification link
            if flight_order_id != 'N/A':
                print(f"\n🔍 Verify Your Booking:")
                print(f"You can check your booking details using the Amadeus Flight Order Management API:")
                print(f"https://developers.amadeus.com/self-service/category/flights/api-doc/flight-order-management/api-reference")
                print(f"\nUse your Flight Order ID: {flight_order_id}")
                print(f"Endpoint: GET /booking/flight-orders/{flight_order_id}")
            
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
                
                # Check if it's a schedule change error or inventory issue
                if ("schedule change" in error_msg or "segment sell failure" in error_msg or
                    "flight no longer available" in error_msg):
                    print(f"\n⏰ Flight availability changed! Auto-searching for updated flights...")
                    
                    if attempt < max_retries:
                        try:
                            # Add small delay to allow airline systems to update
                            print("⏳ Waiting 3 seconds for airline systems to update...")
                            time.sleep(3)
                            
                            print("🔍 Getting fresh flight data...")
                            fresh_options = self.travel_agent.search_and_analyze(self.current_search_params)
                            
                            if fresh_options:
                                new_selection = self.find_similar_flight(fresh_options, self.selected_flight)
                                
                                if new_selection:
                                    self.selected_flight = new_selection
                                    print(f"✅ Found updated flight: {new_selection.airline} - ${new_selection.price:.0f}")
                                    print(f"   New time: {new_selection.departure_time[11:16]}")
                                    continue
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
        raise ValueError("Booking failed: Flight inventory changed and no similar flights were available. Please try searching again with different dates or preferences.")

    def find_similar_flight(self, fresh_options: List, original_flight) -> Optional[FlightOption]:
        """Find a similar flight in fresh search results."""
        try:
            original_time = original_flight.departure_time[11:16]
            original_airline = original_flight.airline
            
            for option in fresh_options:
                if option.airline == original_airline:
                    option_time = option.departure_time[11:16]
                    
                    original_minutes = int(original_time[:2]) * 60 + int(original_time[3:])
                    option_minutes = int(option_time[:2]) * 60 + int(option_time[3:])
                    
                    if abs(original_minutes - option_minutes) <= 120:  # Within 2 hours
                        return option
            
            print("⚠️ Could not find similar flight, selecting cheapest available")
            return fresh_options[0] if fresh_options else None
            
        except Exception as e:
            print(f"⚠️ Error finding similar flight: {e}")
            return fresh_options[0] if fresh_options else None

    def export_flight_data(self, search_params: Dict, flight_options: List[FlightOption]):
        """Export flight search results to timestamped JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flight_search_{timestamp}.json"
            
            export_data = {
                "search_timestamp": datetime.now().isoformat(),
                "search_parameters": search_params,
                "total_flights_found": len(flight_options),
                "flight_analysis": []
            }
            
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
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📁 Flight data exported to: {filename}")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not export flight data: {e}")


if __name__ == "__main__":
    agent = FlightBookingAgent()
    agent.run_autonomous_agent()