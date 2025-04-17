from flask import Flask, render_template, request, session, redirect, url_for, flash
import pickle
import random
import pandas as pd
import zipfile
import os

# Initialize app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ---------- Load and Extract Model Files ----------
model_dir = 'model_files'

# Extract travel_model.pkl if not already extracted
if not os.path.exists(os.path.join(model_dir, 'travel_model.pkl')):
    try:
        with zipfile.ZipFile('travel_model.zip', 'r') as zip_ref:
            zip_ref.extractall(model_dir)
            print("Model extracted successfully.")
    except Exception as e:
        print(f"ERROR: Could not extract model files. Error: {e}")

# Load model and columns
try:
    travel_model = pickle.load(open(os.path.join(model_dir, "travel_model.pkl"), "rb"))
    model_columns = pickle.load(open("model_columns.pkl", "rb"))
    print("Model and columns loaded successfully.")
except Exception as e:
    print(f"ERROR: Could not load model or columns. Error: {e}")

# -------------------- ROUTES --------------------
@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/prediction_form')
def prediction_form():
    return render_template('prediction_form.html')

@app.route('/recommendations', methods=['POST'])
def recommendations():
    start_city = request.form.get('Start City', 'Mumbai')
    traveling_days = request.form.get('Traveling Days', '5')
    package_type = request.form.get('Package Type', 'Standard')

    if not traveling_days.isdigit():
        traveling_days = '5'

    recommendations_list = []

    for i in range(5):
        destination = get_destination_for_package(package_type)
        hotel_category = get_hotel_for_package(package_type)
        airline = get_airline_for_city(start_city)

        form_data = {
            'Start City': start_city,
            'Traveling Days': traveling_days,
            'Package Type': package_type,
            'Destination': destination,
            'Airline': airline,
            'Hotel Category': hotel_category,
            'Cancellation Rules': 'Free cancellation up to 7 days before travel',
            'Package Name': f"{destination} {package_type} Package",
            'Company': 'TravelSense',
            'Places Covered': get_places_for_destination(destination),
            'Travel Date': '2025-05-15',
            'Page Url': 'https://travelsense.com/packages',
            'Destination Count': '1',
            'Hotel Details': get_hotel_details(hotel_category),
            'Onwards Return Flight Time': get_flight_time(start_city, destination),
            'Itinerary': get_itinerary(destination, traveling_days),
            'Destination List': destination,
            'Flight Stops Encoded': '0',
            'Sightseeing Places Covered': get_sightseeing(destination)
        }

        recommendation = {
            'id': i,
            'start_city': start_city,
            'destination': destination,
            'traveling_days': int(traveling_days),
            'package_type': package_type,
            'hotel_category': hotel_category,
            'airline': airline,
            'flight_time': form_data['Onwards Return Flight Time'],
        }

        recommendations_list.append(recommendation)

    session['recommendations_list'] = recommendations_list
    return render_template('recommendations.html', recommendations=recommendations_list)

@app.route('/details/<destination>')
def details(destination):
    recommendations_list = session.get('recommendations_list', [])
    selected = next((item for item in recommendations_list if item['destination'] == destination), None)

    if selected:
        selected['itinerary'] = get_itinerary(destination, selected['traveling_days']).split('|')
        selected['places_covered'] = get_places_for_destination(destination)
        selected['sightseeing'] = get_sightseeing(destination)
        selected['hotel_details'] = get_hotel_details(selected['hotel_category'])
        selected['cancellation_rules'] = 'Free cancellation up to 7 days before travel'
        return render_template('detailed_results.html', package=selected)
    else:
        return "Invalid selection", 404

# ------------------ Helper Functions ------------------

def get_destination_for_package(package_type):
    destinations = {
        'Budget': ['Goa', 'Jaipur', 'Agra', 'Rishikesh', 'Varanasi'],
        'Standard': ['Kerala', 'Himachal Pradesh', 'Udaipur', 'Darjeeling', 'Amritsar'],
        'Premium': ['Andaman', 'Kashmir', 'Leh Ladakh', 'Sikkim', 'Coorg'],
        'Luxury': ['Maldives', 'Thailand', 'Dubai', 'Singapore', 'Malaysia']
    }
    return random.choice(destinations.get(package_type, destinations['Standard']))

def get_airline_for_city(city):
    airlines = ['IndiGo', 'Air India', 'SpiceJet', 'Vistara', 'GoAir', 'AirAsia']
    return random.choice(airlines)

def get_hotel_for_package(package_type):
    hotels = {
        'Budget': '3-star',
        'Standard': '3-star',
        'Premium': '4-star',
        'Luxury': '5-star'
    }
    return hotels.get(package_type, '3-star')

def get_hotel_details(category):
    if category == '3-star':
        return 'Comfortable rooms with basic amenities, breakfast included'
    elif category == '4-star':
        return 'Spacious rooms with premium amenities, breakfast and dinner included'
    elif category == '5-star':
        return 'Luxury accommodation with all meals, spa access, and premium services'
    else:
        return 'Standard accommodation with necessary amenities'

def get_flight_time(start, destination):
    return f'Departure: 10:00 AM, Return: 4:30 PM'

def get_places_for_destination(destination):
    places = {
        'Goa': 'Calangute Beach, Baga Beach, Fort Aguada, Dudhsagar Falls',
        'Jaipur': 'Amer Fort, Hawa Mahal, City Palace, Jantar Mantar',
        'Agra': 'Taj Mahal, Agra Fort, Fatehpur Sikri',
        'Rishikesh': 'Lakshman Jhula, Neelkanth Mahadev Temple, Triveni Ghat',
        'Varanasi': 'Kashi Vishwanath Temple, Dashashwamedh Ghat, Sarnath, Manikarnika Ghat',
        'Kerala': 'Munnar, Alleppey, Kovalam, Wayanad',
        'Himachal Pradesh': 'Shimla, Manali, Dharamshala, Dalhousie',
        'Andaman': 'Port Blair, Havelock Island, Neil Island, Ross Island',
        'Kashmir': 'Srinagar, Gulmarg, Pahalgam, Sonamarg',
        'Leh Ladakh': 'Pangong Lake, Nubra Valley, Magnetic Hill, Shanti Stupa',
        'Maldives': 'Male, Maafushi Island, Biyadhoo Island',
        'Thailand': 'Bangkok, Pattaya, Phuket, Krabi',
        'Dubai': 'Burj Khalifa, Palm Jumeirah, Dubai Mall, Dubai Marina',
        'Singapore': 'Marina Bay Sands, Sentosa Island, Gardens by the Bay, Universal Studios Singapore'
    }
    return places.get(destination, f'Popular attractions in {destination}')

def get_itinerary(destination, days):
    days = int(days)
    base_itineraries = {
        'Goa': [
            'Day 1: Arrival and check-in, beach visit',
            'Day 2: North Goa beaches tour',
            'Day 3: South Goa exploration',
            'Day 4: Dudhsagar Falls excursion',
            'Day 5: Spice plantation visit and departure'
        ],
        'Kerala': [
            'Day 1: Arrival in Kochi, local sightseeing',
            'Day 2: Travel to Munnar, tea garden visit',
            'Day 3: Munnar exploration and activities',
            'Day 4: Travel to Alleppey, houseboat check-in',
            'Day 5: Backwater cruise and departure'
        ],
        'Himachal Pradesh': [
            'Day 1: Arrival in Shimla, Mall Road visit',
            'Day 2: Kufri and local sightseeing',
            'Day 3: Travel to Manali',
            'Day 4: Solang Valley and Rohtang Pass',
            'Day 5: Manali local sightseeing and departure'
        ]
    }
    itinerary = base_itineraries.get(destination, [
        f'Day 1: Arrival in {destination}, hotel check-in and local exploration',
        f'Day 2: Visit to popular attractions in {destination}',
        f'Day 3: Adventure activities and sightseeing',
        f'Day 4: Cultural experiences and shopping',
    ])
    if days < len(itinerary):
        return '|'.join(itinerary[:days])
    elif days > len(itinerary):
        for i in range(len(itinerary) + 1, days + 1):
            itinerary.append(f'Day {i}: Additional sightseeing and activities')
    return '|'.join(itinerary)

def get_sightseeing(destination):
    df = pd.read_csv('C:/Users/sit421/Desktop/DestinationDiscoveries/final_final_travel_exploded.zip')
    sightseeing_data = df[df['Destination List'] == destination]['Places Covered'].values
    if len(sightseeing_data) > 0:
        return sightseeing_data[0]
    else:
        return f"No sightseeing data available for {destination}"

# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run(debug=True)
