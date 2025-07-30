"""
Travel agent module for handling flight search, analysis, and booking operations.
"""

import json
from typing import Dict, List
from amadeus import ResponseError
from models import FlightOption
from flight_analyzer import FlightAnalyzer


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
        """Book the selected flight using SDK method (following Django demo pattern)."""
        try:
            print("📋 Processing booking...")
            
            # Step 1: Refresh flight data to avoid schedule changes
            print("🔄 Validating flight availability...")
            validated_flight = self._validate_flight_pricing(flight_option.flight_data)
            
            # Step 2: Fix traveler IDs to match flight offer pricing
            corrected_travelers = self._match_traveler_ids(validated_flight, travelers)
            
            print("🔍 Debug - Sending booking request...")
            print(f"🔍 Debug - Flight offer ID: {validated_flight.get('id', 'No ID')}")
            print(f"🔍 Debug - Original travelers: {len(travelers)}")
            print(f"🔍 Debug - Corrected travelers: {len(corrected_travelers)}")
            print(f"🔍 Debug - Traveler IDs: {[t['id'] for t in corrected_travelers]}")
            
            # Use SDK method for booking (following Django demo pattern)
            # Note: Contact info is included in traveler data, not as separate parameter
            response = self.amadeus_client.booking.flight_orders.post(
                [validated_flight], corrected_travelers
            )
            
            print("✅ Booking successful!")
            return response.data
            
        except ResponseError as e:
            # Better error handling
            print(f"🔍 Debug - Response status: {e.response.status_code}")
            print(f"🔍 Debug - Response body: {e.response.body}")
            
            # Check for segment sell failure specifically
            is_segment_sell_failure = False
            try:
                error_body = json.loads(e.response.body) if e.response.body else {}
                if 'errors' in error_body:
                    for error in error_body['errors']:
                        error_detail = error.get('detail', '').lower()
                        error_code = error.get('code')
                        print(f"❌ API Error: {error.get('detail', 'Unknown error')}")
                        if 'source' in error:
                            print(f"   Field: {error['source'].get('parameter', 'Unknown field')}")
                        
                        # Detect segment sell failure
                        if ('segment sell failure' in error_detail or 
                            'could not sell segment' in error_detail or
                            error_code == 34651):
                            is_segment_sell_failure = True
            except:
                pass
            
            # Raise appropriate error type for retry logic
            if is_segment_sell_failure:
                raise ValueError("SEGMENT SELL FAILURE - Flight no longer available for booking")
            else:
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
        """Validate flight pricing to get fresh schedule data using SDK method."""
        try:
            # Use SDK method for pricing validation (following Django demo pattern)
            response = self.amadeus_client.shopping.flight_offers.pricing.post(flight_data)
            
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
    
    def get_booking_details(self, flight_order_id: str) -> Dict:
        """Retrieve booking details using Flight Order Management API."""
        try:
            print(f"🔍 Retrieving booking details for order: {flight_order_id}")
            
            # Use SDK method to get flight order details
            response = self.amadeus_client.booking.flight_order(flight_order_id).get()
            
            print("✅ Booking details retrieved successfully")
            return response.data
            
        except ResponseError as e:
            print(f"❌ Could not retrieve booking: {e.description}")
            raise ValueError(f"Booking retrieval failed: {e.description}")
        except Exception as e:
            print(f"❌ Unexpected error retrieving booking: {e}")
            raise ValueError(f"Unexpected booking retrieval error: {e}")