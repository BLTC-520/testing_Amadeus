"""
Flight analysis and ranking module.
"""

from typing import List, Dict, Optional
from models import FlightOption


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