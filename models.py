"""
Data models for the flight booking system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


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