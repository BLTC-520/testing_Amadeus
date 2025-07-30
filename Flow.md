# 🎯 Autonomous Flight Booking Agent - Demo Guide

## Overview
Complete autonomous flight booking system using Amadeus APIs + OpenAI for natural language processing.

## File Structure & Key Functions

### 1. **flight_booking_agent.py** (Main Orchestrator)
```
📁 flight_booking_agent.py
├── 🎯 FlightBookingAgent.run_autonomous_agent() [Line 74-123]
│   └── Main CLI loop and user interaction
├── 🔄 FlightBookingAgent.execute_agent_workflow() [Line 195-235]
│   └── 7-phase booking workflow orchestration
├── 🛠️ FlightBookingAgent.attempt_booking_with_retry() [Line 244-279]
│   └── Error handling with automatic retry logic
├── 🔍 FlightBookingAgent.check_booking() [Line 136-193]
│   └── Booking verification functionality
└── 🎯 FlightBookingAgent.find_similar_flight() [Line 286-307]
    └── Smart flight matching for retries
```

**Key Demo Lines:**
- **Line 85**: Demo instructions displayed to user
- **Line 103-112**: Booking verification command handling
- **Line 208-213**: Verification link generation
- **Line 230-233**: SEGMENT SELL FAILURE detection
- **Line 238-239**: 3-second retry delay

### 2. **user_agent.py** (Natural Language & UI)
```
📁 user_agent.py
├── 🧠 UserAgent.parse_initial_request() [Line 20-78]
│   └── OpenAI integration for natural language parsing
├── 👤 UserAgent.collect_traveler_info() [Line 98-193]
│   └── Auto-fill passenger data functionality
├── 📋 UserAgent.present_options() [Line 80-96]
│   └── Flight options presentation
└── 📞 UserAgent.collect_booking_contact() [Line 195-240]
    └── Auto-fill contact information
```

**Key Demo Lines:**
- **Line 26-57**: OpenAI prompt engineering for flight parsing
- **Line 103-116**: Auto-fill passenger profile data
- **Line 123**: Auto-fill prompt ("Use auto-fill with saved profile? (y/n)")
- **Line 88-95**: Top 3 flight options formatting

### 3. **travel_agent.py** (Amadeus API Integration)
```
📁 travel_agent.py
├── 🔍 TravelAgent.search_and_analyze() [Line 21-62]
│   └── Flight search with dynamic parameters
├── 💳 TravelAgent.book_flight() [Line 64-111]
│   └── 3-step booking with SDK methods
├── 🔄 TravelAgent._validate_flight_pricing() [Line 163-178]
│   └── Price confirmation (Step 2 of 3)
├── 👥 TravelAgent._match_traveler_ids() [Line 113-157]
│   └── Traveler ID synchronization
└── 🔍 TravelAgent.get_booking_details() [Line 180-196]
    └── Booking verification API call
```

**Key Demo Lines:**
- **Line 46**: Amadeus flight search API call
- **Line 84-86**: SDK booking method (proper 3-step flow)
- **Line 167**: Price validation using SDK
- **Line 108-112**: SEGMENT SELL FAILURE error detection
- **Line 186**: Booking details retrieval

### 4. **flight_analyzer.py** (Flight Ranking)
```
📁 flight_analyzer.py
├── 🎯 FlightAnalyzer.analyze_flights() [Line 19-34]
│   └── Price-based ranking (cheapest first)
├── ✈️ FlightAnalyzer._create_flight_option() [Line 36-76]
│   └── FlightOption object creation
└── 💡 FlightAnalyzer._generate_simple_recommendation() [Line 78-99]
    └── Simple recommendation logic
```

**Key Demo Lines:**
- **Line 32**: Sort by price (cheapest first)
- **Line 64**: Simple recommendation generation
- **Line 83-97**: Budget comparison logic

### 5. **models.py** (Data Structures)
```
📁 models.py
├── 📊 FlightOption [Line 10-22]
│   └── Flight data container with analysis
└── 💬 AgentMessage [Line 24-31]
    └── Agent communication structure
```

## Demo Script

### 1. **Start the Agent**
```bash
cd /Users/brianhar/Desktop/testingAmadues/amadeus-python
python flight_booking_agent.py
```

### 2. **Natural Language Search**
```
🗣️ What flight do you need? Find me cheap flights from KUL to SIN tomorrow
```

### 3. **Flight Selection**
```
Which option would you like me to book? (1, 2, 3, or 'show more' for other options)
Your choice: 1
```

### 4. **Auto-fill Demo**
```
=== Adult Traveler 1 ===
Use auto-fill with saved profile? (y/n): y
✅ Using auto-fill...
```

### 5. **Booking Verification**
```
🗣️ What flight do you need? check eJzTd9c3N3b2C%2FUCAApkAkA%3D
```

## Key Technical Features

### 🔄 **3-Step Amadeus Flow** (travel_agent.py)
1. **Search**: `amadeus.shopping.flight_offers_search.get()` [Line 46]
2. **Price**: `amadeus.shopping.flight_offers.pricing.post()` [Line 167]
3. **Book**: `amadeus.booking.flight_orders.post()` [Line 84-86]

### 🧠 **OpenAI Integration** (user_agent.py)
- **Model**: GPT-3.5-turbo [Line 61]
- **Prompt Engineering**: Lines 26-57
- **JSON Response Parsing**: Lines 70-75

### 🛠️ **Error Recovery** (flight_booking_agent.py)
- **SEGMENT SELL FAILURE Detection**: Lines 230-233
- **Automatic Retry**: Lines 236-242
- **Smart Flight Matching**: Lines 286-307

### 📊 **Auto-fill System** (user_agent.py)
- **Default Profile**: Lines 103-116
- **Quick Demo Mode**: Line 123
- **Contact Auto-fill**: Lines 201-213

## Environment Setup
```bash
# Required credentials (hardcoded for demo)
AMADEUS_CLIENT_ID='DUiNUoJvcxReIPZmEt5YeRSmFJ3FUWnA'
AMADEUS_CLIENT_SECRET='JaH713c6Iko4dtcp'
OPENAI_API_KEY='sk-proj-...'
```

## Demo Tips
- **Use auto-fill (y)** for speed demonstration
- **Try routes**: "KUL to SIN", "BKK to KUL", "JFK to LAX"
- **Show error recovery** by booking popular flights
- **Demonstrate verification** with returned PNR
- **Mention test environment** - safe for demos

## Success Metrics
✅ **Modular Architecture**: 5 separate modules  
✅ **Natural Language Processing**: OpenAI integration  
✅ **Autonomous Booking**: Complete 3-step flow  
✅ **Error Recovery**: Automatic retry system  
✅ **User Experience**: Auto-fill + verification  
✅ **Production Ready**: Proper SDK usage  

