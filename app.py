from flask import Flask, render_template, request, jsonify
import json
import os
from serpapi import GoogleSearch
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from datetime import datetime

app = Flask(__name__)

SERPAPI_KEY = "98e1c8e5dea7430a7832b85fa33a2a1e028fd47226f0bed9b07550f19fadb7e7"
GOOGLE_API_KEY = "AIzaSyDKazkFS08O2Z6VCGDB9NBwgt3MM9nWZv8"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

def format_datetime(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
        return dt.strftime("%b-%d, %Y | %I:%M %p")
    except Exception as e:
        return "N/A"

def fetch_flights(source, destination, departure_date, return_date):
    params = {
        "engine": "google_flights",
        "departure_id": source,
        "arrival_id": destination,
        "outbound_date": str(departure_date),
        "return_date": str(return_date),
        "currency": "INR",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results

def extract_cheapest_flights(flight_data):
    best_flights = flight_data.get("best_flights", [])
    sorted_flights = sorted(best_flights, key=lambda x: x.get("price", float("inf")))[:3]
    return sorted_flights

# Initialize Agents
researcher = Agent(
    name="Researcher",
    instructions=[
        "Identify the travel destination specified by the user."
        "Gather detailed information on the destination, including climate, culture, and safety tips."
        "Find popular attractions, landmarks, and must-visit places."
        "Search for activities that match the user's interests and travel guides"
        "Provide well-structured summaries with key insights and recommendations."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[SerpApiTools(api_key=SERPAPI_KEY)],
    add_datetime_to_instructions=True
)

planner = Agent(
    name="Planner",
    instructions=[
        "Gather details about the user's travel preferences and budget.",
        "Create a detailed itinerary with scheduled activities and estimated costs."
        "Ensure the itinerary includes transportation options and travel estimates.",
        "Optimize the schedule for convenience and enjoyment."
        "Present the itinerary in a structured format."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

hotel_restaurant_finder = Agent(
    name="Hotel & Restaurant Finder",
    instructions=[
        "Identify key locations in the user's travel itinerary.",
        "Search for highly rated hotels near those locations.",
        "Search for top-rated restaurants based on cuisine preferences and proximity."
        "Prioritize results based on user preferences, ratings, and availability."
        "Provide direct booking links or reservation where possible."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[SerpApiTools(api_key=SERPAPI_KEY)],
    add_datetime_to_instructions=True,
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_plan', methods=['POST'])
def generate_plan():
    # Get form data
    source = request.form.get('source', 'BOM')
    destination = request.form.get('destination', 'DEL')
    num_days = int(request.form.get('num_days', 5))
    travel_theme = request.form.get('travel_theme', 'Couple Getaway')
    activity_preferences = request.form.get('activity_preferences', 'Relaxing on the beach, exploring historical sites')
    departure_date = request.form.get('departure_date')
    return_date = request.form.get('return_date')
    budget = request.form.get('budget', 'Economy')
    flight_class = request.form.get('flight_class', 'Economy')
    hotel_rating = request.form.get('hotel_rating', 'Any')
    visa_required = 'visa_required' in request.form
    travel_insurance = 'travel_insurance' in request.form
    currency_converter = 'currency_converter' in request.form
    
    # Process data
    flight_data = fetch_flights(source, destination, departure_date, return_date)
    cheapest_flights = extract_cheapest_flights(flight_data)
    
    # Research attractions & activities
    research_prompt = (
        f"Research the best attractions and activities in {destination} for a {num_days}-days {travel_theme.lower()} trip."
        f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}."
        f"Hotel Rating: {hotel_rating}. Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}."
    )
    research_results = researcher.run(research_prompt, stream=False)
    
    # Search for hotels & restaurants
    hotel_restaurant_prompt = (
        f"Find the best hotels and restaurants near popular attractions in {destination} for a {travel_theme.lower()} trip "
        f"Budget: {budget}. Hotel Rating: {hotel_rating}. Preferred activities: {activity_preferences}."
    )
    hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)
    
    # Create personalized itinerary
    planning_prompt = (
        f"Based on the following data, create a {num_days}-days itinerary for a {travel_theme.lower()} trip to {destination}."
        f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. Hotel Rating: {hotel_rating}."
        f"Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}. Research: {research_results.content}."
        f"Flights: {json.dumps(cheapest_flights)}. Hotels & Restaurants: {hotel_restaurant_results.content}."
    )
    itinerary = planner.run(planning_prompt, stream=False)
    
    # Format flight data for the template
    formatted_flights = []
    for flight in cheapest_flights:
        airline_logo = flight.get("airline_logo", "")
        airline_name = flight.get("airline", "Unknown Airline")
        price = flight.get("price", "Not Available")
        total_duration = flight.get("total_duration", "N/A")

        flights_info = flight.get("flights", [{}])
        departure = flights_info[0].get("departure_airport", {})
        arrival = flights_info[0].get("arrival_airport", {})
        airline_name = flights_info[0].get("airline", "Unknown Airline")

        departure_time = format_datetime(departure.get("time", "N/A"))
        arrival_time = format_datetime(arrival.get("time", "N/A"))
        
        # Handle booking links
        booking_link = "#"
        departure_token = flight.get("departure_token", "")
        if departure_token:
            params = {
                "engine": "google_flights",
                "departure_id": source,
                "arrival_id": destination,
                "outbound_date": str(departure_date),
                "return_date": str(return_date),
                "currency": "INR",
                "hl": "en",
                "api_key": SERPAPI_KEY,
                "departure_token": departure_token
            }
            search_with_token = GoogleSearch(params)
            results_with_token = search_with_token.get_dict()
            
            best_flights_token = results_with_token.get('best_flights', [])
            if best_flights_token and isinstance(best_flights_token, list):
                booking_token = best_flights_token[0].get('booking_token', '')
                if booking_token:
                    booking_link = f"https://www.google.com/travel/flights?tfs={booking_token}"
                else:
                    print("No booking_token found in the best_flights data")
            else:
                print("No best_flights returned from SerpAPI with departure_token")
        formatted_flights.append({
            'airline_logo': airline_logo,
            'airline_name': airline_name,
            'departure_time': departure_time,
            'arrival_time': arrival_time,
            'total_duration': total_duration,
            'price': price,
            'booking_link': booking_link
        })
    
    return render_template(
        'results.html',
        destination=destination,
        travel_theme=travel_theme,
        flights=formatted_flights,
        hotels_restaurants=hotel_restaurant_results.content,
        itinerary=itinerary.content,
        num_days=num_days
    )

if __name__ == '__main__':
    app.run(debug=True)