# Autonomous Flight Booking Agent Implementation

A complete autonomous flight booking system built with **Amadeus Travel APIs** and **OpenAI GPT-3.5-turbo** (cheap!) for natural language processing.

## 🚀 Features

- **🗣️ Natural Language Search**: "Find me cheap flights from KUL to BKK, direct flight, budget $400"
- **🤖 Autonomous Booking**: Complete 3-step Amadeus booking flow (Search → Price → Book)
- **⚡ Auto-fill System**: Quick demo mode with pre-saved traveler information
- **🧠 Smart Flight Analysis**: Price-based ranking with intelligent recommendations
- **🔄 Error Recovery**: Automatic retry with fresh flights on schedule changes
- **✅ Booking Verification**: Built-in checker + direct API links
- **📦 Modular Architecture**: Clean, maintainable code structure

## 📋 Quick Start

### 1. Prerequisites

```bash
# Install required packages
pip install -r requirements.txt

# (I have added `amadeus, openai` into the original SDK's) requirements.txt)
```

### 2. API Configuration

**⚠️ IMPORTANT: Configure your API credentials before running**

Edit `flight_booking_agent.py` at **lines 36-38**:

```python
class FlightBookingAgent:
    def __init__(self):
        # hardcoded credentials for dev (I didn't set up .env for ease of testing)
        self.amadeus_client_id = 'YOUR_CLIENT_ID'      # ← Replace with your Amadeus client ID
        self.amadeus_client_secret = 'YOUR_CLIENT_SECRET'  # ← Replace with your Amadeus client secret  
        self.openai_api_key = 'YOUR_KEY_HERE'          # ← Replace with your OpenAI API key
```

**Get your API keys:**
- **Amadeus**: Register at [developers.amadeus.com](https://developers.amadeus.com/register)
- **OpenAI**: Get API key at [platform.openai.com](https://platform.openai.com/api-keys)

### 3. Run the Agent

```bash
python flight_booking_agent.py
```

## 🎯 Demo Usage

### Natural Language Flight Search
```
🗣️ What flight do you need? Find me cheap flights from KUL to SIN tomorrow

🧠 User Agent: Understanding your request...
✓ Understood: KUL → SIN
🔍 Travel Agent: Searching and analyzing flights...
✅ Found 20 flight options

📋 User Agent: Here are the best options I found:
1. OD - $53
   ⏰ 2025-07-31 08:35 → 11:40
   ✈️ Direct flight • Great value

Which option would you like me to book? (1, 2, 3, or 'show more')
Your choice: 1
```

### Auto-fill Demo Mode
```
=== Adult Traveler 1 ===
Use auto-fill with saved profile? (y/n): y
✅ Using auto-fill...
Name: BRIAN HAR
DOB: 2003-05-20
Email: sze@gmail.com
Passport: ACB821909
```

### Booking Verification
```
🗣️ What flight do you need? check eJzTd9c3N3b2C%2FUCAApkAkA%3D

🔍 Checking booking: eJzTd9c3N3b2C%2FUCAApkAkA%3D
✅ Booking details retrieved successfully

📋 Booking Details:
Flight Order ID: eJzTd9c3N3b2C%2FUCAApkAkA%3D
PNR Reference: ABC123
Total Price: USD 53
```

## 🏗️ Architecture

### File Structure
```
📁 amadeus-python/
├── 🎯 flight_booking_agent.py    # Main CLI orchestrator
├── 🧠 user_agent.py             # Natural language processing & UI
├── ✈️ travel_agent.py           # Amadeus API integration
├── 📊 flight_analyzer.py        # Flight ranking & analysis
├── 📋 models.py                 # Data structures
├── 📖 DEMO_GUIDE.md            # Complete demo documentation
└── 📚 README.md                # This file
```

### Key Components

| Component | File | Key Functions | Configuration |
|-----------|------|---------------|---------------|
| **Main CLI** | `flight_booking_agent.py` | Lines 74-123: Main loop<br>Lines 195-235: Workflow<br>Lines 244-279: Error recovery | **Lines 36-38**: API credentials |
| **Natural Language** | `user_agent.py` | Lines 20-78: OpenAI parsing<br>Lines 98-193: Auto-fill system | Uses OpenAI GPT-3.5-turbo |
| **Flight APIs** | `travel_agent.py` | Lines 46: Flight search<br>Lines 84-86: Booking<br>Lines 167: Price validation | Uses Amadeus SDK methods |
| **Flight Analysis** | `flight_analyzer.py` | Lines 19-34: Price ranking<br>Lines 78-99: Recommendations | Price-based sorting |

## 🔧 Configuration Details

### API Credentials Location
**File**: `flight_booking_agent.py`  
**Lines**: 36-38

```python
# CONFIGURE THESE VALUES:
self.amadeus_client_id = 'YOUR_CLIENT_ID'        # Line 36
self.amadeus_client_secret = 'YOUR_CLIENT_SECRET'  # Line 37  
self.openai_api_key = 'YOUR_KEY_HERE'            # Line 38
```

### Auto-fill Profile Configuration
**File**: `user_agent.py`  
**Lines**: 103-116

```python
# Default profile (customize for your demo)
default_profile = {
    "first_name": "BRIAN",           # Line 104
    "last_name": "HAR",              # Line 105
    "date_of_birth": "2003-05-20",   # Line 106
    "email": "sze@gmail.com",        # Line 108
    "passport_number": "ACB821909",  # Line 111
    # ... more fields
}
```

## 🎭 Demo Commands

| Command | Example | Description |
|---------|---------|-------------|
| **Flight Search** | `Find flights KUL to SIN budget $100` | Natural language flight search |
| **Booking Verification** | `check eJzTd9c3N3b2C%2FUCAApkAkA%3D` | Verify existing booking |
| **Exit** | `quit` or `exit` | Exit the application |

## 🛠️ Technical Implementation

### 3-Step Amadeus Booking Flow
1. **Search**: `amadeus.shopping.flight_offers_search.get()` (Line 46 in `travel_agent.py`)
2. **Price**: `amadeus.shopping.flight_offers.pricing.post()` (Line 167 in `travel_agent.py`)  
3. **Book**: `amadeus.booking.flight_orders.post()` (Lines 84-86 in `travel_agent.py`)

### Error Recovery System
- **Detection**: Lines 230-233 in `flight_booking_agent.py`
- **Retry Logic**: Lines 236-242 with 3-second delay
- **Smart Matching**: Lines 286-307 for similar flight selection

### OpenAI Integration
- **Model**: GPT-3.5-turbo (Line 61 in `user_agent.py`)
- **Prompt Engineering**: Lines 26-57 in `user_agent.py`
- **Response Parsing**: Lines 70-75 in `user_agent.py`

### Test Environment (Default)
- Uses Amadeus test APIs
- Safe for development and demos
- Limited flight data available

## 📖 Documentation
- **Complete Demo Guide**: See `DEMO_GUIDE.md` for detailed walkthrough
  
## 🚦 Troubleshooting

### Common Issues

| Issue | Solution | File:Line |
|-------|----------|-----------|
| **"Could not parse user request"** | Check OpenAI API key configuration | `user_agent.py:78` |
| **"Flight search failed"** | Check Amadeus API credentials, look at `test_connection.py` to setup up client | `travel_agent.py:60` |
| **"SEGMENT SELL FAILURE"** | System will auto-retry with fresh flights | `travel_agent.py:118` |

### Debug Mode
Enable debug logging by modifying line 57 in `flight_booking_agent.py`:
```python
self.amadeus_client = Client(
    client_id=self.amadeus_client_id,
    client_secret=self.amadeus_client_secret,
    log_level='debug'  # Add this line
)
```

---

**Ready for Demo**: Configure API keys → Run `python flight_booking_agent.py` → Try "Find flights KUL to SIN budget $100"