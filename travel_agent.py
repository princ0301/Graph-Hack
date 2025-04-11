import streamlit as st
import json
import os 
from serpapi import GoogleSearch
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from datetime import datetime

st.set_page_config(page_title="AI Travel Planner", layout="wide")
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #ff5733;
    }
    .subtitle {
        text-align: center;
        font-size: 20px;
        color: #555;
    }
    .stSider > div {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 clss="title">AI Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">A chatbot for booking hotels</p>', unsafe_allow_html=True)

st.markdown('### Where are you headed?')
source = st.text_input(" Departure city (IATA code):", "BOM")
destination = st.text_input(" Destination city (IATA code):", "DEL")

st.markdown("### Plan Your Adventure")
num_days = st.sidebar.slider("Trip Duration (days)", 1, 14, 5)
travel_theme = st.selectbox(
    "Select your travel theme",
    ["Couple Getway", "Family Vacation", "Adventure Trip", "Solo Exploration"]
)

st.markdown("---")

st.markdown(
    f"""
    <div style="
        text-align: centre;
        padding: 15px;
        background-color: #ffecd1;
        border-radius: 10px;
        margin-top: 20px;
    ">
        <h3> Your {travel_theme} to {destination} is about to begin! </h3>
        <p> Let's find the best flights, stays, and experiences for your unforgetable journey.. </p>
    </div>
    """,
    unsafe_allow_html=True,
)

def format_datetime(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
        return dt.strftime("%b-%d, %Y | %I:%M %p")
    except Exception as e:
        return "N/A"
    
activity_preferences = st.text_area(
    "What activities do you enjoy? (e.g., relaxing on the beach, exploring historical sites, nightlife, adventure)",
    "Relaxing on the beach, exploring historical sites"
)

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

st.sidebar.title("Travel Assistant")
st.sidebar.subheader("Personalized Your Trip")

budget = st.sidebar.radio(" Budget Perference:", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("Flight Class:", ["Economy", "Business", "First Class"])
hotel_rating = st.sidebar.selectbox("Perefered Hotel Rating:", ["Any", "3", "4", "5"])

st.sidebar.subheader("Packing Checklist")
packing_list = {
    "Clothes": True,
    "Comfortable Footwear": True,
    "Sunglasses & Sunscreen": False,
    "Travel Guidebook": False,
    "Medications & First-Aid": True
}
for item, checked in packing_list.items():
    st.sidebar.checkbox(item, value=checked)

st.sidebar.subheader("Travel Essentials")
visa_required = st.sidebar.checkbox("Check Visa Requirements")
travel_insurance = st.sidebar.checkbox("Get Travel Insurance")
currency_converter = st.sidebar.checkbox("Currency Exchange rates")

SERPAPI_KEY = "98e1c8e5dea7430a7832b85fa33a2a1e028fd47226f0bed9b07550f19fadb7e7"
GOOGLE_API_KEY = "AIzaSyDKazkFS08O2Z6VCGDB9NBwgt3MM9nWZv8"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

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
    name="Planer",
    instructions=[
        "Gather details about the user's travel preferences and budget.",
        "Create a detiled itinerary with schedule activities and estimated costs."
        "Ensure the itinerary includes transportation options and travel estimates.",
        "Optimize the schedule for convenience and enjoyment."
        "Present the itinerary in a structured format."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

hotel_restaurent_finder = Agent(
    name="Hotel & Restaurent Finder",
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

if st.button("Generate Travel Plan"):
    with st.spinner(" Fetching best flights options..."):
        flight_data = fetch_flights(source, destination, departure_date, return_date)
        cheapest_flights = extract_cheapest_flights(flight_data)

    with st.spinner("Researching best attractions & activities..."):
        research_prompt = (
            f"Research the best attractions and activities in {destination} for a {num_days}-days {travel_theme.lower()} trip."
            f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}."
            f"Hotel Rating: {hotel_rating}. Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}."
        )
        research_results = researcher.run(research_prompt, stream=False)

    with st.spinner("Searching for hotels & restaurants..."):
        hotel_restaurent_prompt = (
            f"Find the best hotels and restaurants near popular attractions in {destination} for a {travel_theme.lower()} trip"
            f"Budget: {budget}. Hotel Rating: {hotel_rating}. Prefered activities: {activity_preferences}."
        )
        hotel_restaurent_results = hotel_restaurent_finder.run(hotel_restaurent_prompt, stream=False)

    with st.spinner("Creating your presonalized itinerary..."):
        planning_prompt = (
            f"Based on the following data, create a {num_days}-days itinerary for a {travel_theme.lower()} trip to {destination}."
            f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. Hotel Rating: {hotel_rating}."
            f"Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}. Reserch: {research_results.content}."
            f"Flights: {json.dumps(cheapest_flights)}. Hotels & Restaurants: {hotel_restaurent_results.content}."
        )
        itineary = planner.run(planning_prompt, stream=False)

    
    st.subheader("Cheapest Flight Options")
    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
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

                departure_token = flight.get("departure_token", "")

                if departure_token:
                    params_with_token = {
                        **params,
                        "departure_token": departure_token
                    }
                    search_with_token = GoogleSearch(params_with_token)
                    results_with_booking = search_with_token.get_dict()

                    booking_options = results_with_booking['best_flights'][idx]['booking_token']

                booking_link = f"https://www.google.com/travel/flights?tfs="+booking_options if booking_options else "#"
                print(booking_link)

                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid #ddd;
                        border-radius: 10px;
                        padding: 15px;
                        text-align: centre;
                        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
                        background-color: #f9f9f9;
                        margin-bottom: 20px;
                    ">
                        <img src="{airline_logo}" width="100", alt="Flight Logo" />
                        <h3 style="margin: 10px 0;">{airline_name}</h3>
                        <p><strong>Departure:</strong> {departure_time}</p>
                        <p><strong>Arrival:</strong> {arrival_time}</p>
                        <p><strong>Total Duration:</strong> {total_duration}</p>
                        <p><strong>Price:</strong> {price}</p> 
                        <a href="{booking_link}" target="_blank" style="
                            display: inline-block;
                            padding: 10px 20px;
                            font-size: 16px;
                            font-weight: bold;
                            background-color: #007bff;
                            color: #fff;
                            text-decoration: none;
                            border-radius: 5px; 
                            margin-top: 10px; 
                        ">Book Now</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    else:
        st.warning("No flight data available")

    st.subheader("Hotels & restaurants")
    st.write(hotel_restaurent_results.content)

    st.subheader("Your Pesonalized Ininerary")
    st.write(itineary.content)

    st.success("Travel plan generated successfully!")
