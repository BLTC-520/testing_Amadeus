from amadeus import Client, ResponseError

amadeus = Client(
    client_id='', # YOUR CLIENT_ID
    client_secret='' # YOUR CLIENT_SECRET
)

try:
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='MAD',
        destinationLocationCode='ATH',
        departureDate='2025-12-01',
        adults=1)
    print(response.data)
except ResponseError as error:
    print(error)