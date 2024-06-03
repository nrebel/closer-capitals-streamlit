import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from math import radians, sin, cos, sqrt, atan2

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('resources/worldcities.csv')
    return df

# Haversine function to calculate distance between two points on the Earth
def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0  # Earth radius in kilometers
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    a = max(0, min(1, a))  # Clamp 'a' to the range [0, 1]
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Function to find the city with most closer capitals
def find_city_with_most_closer_capitals(country, file_path):
    # Load data
    world_cities = pd.read_csv(file_path)
    if 'country' not in world_cities.columns:
        raise KeyError("The column 'country' is not found in the data.")

    # Filter capitals and cities in the specified country
    capitals = world_cities[world_cities['capital'] == 'primary'][['city', 'lat', 'lng', 'country']]
    capitals = capitals.drop_duplicates(subset=['country'])

    country_cities = world_cities[world_cities['country'] == country][['city', 'lat', 'lng']]
    country_capital = capitals[capitals['country'] == country]

    results = []

    if len(country_cities) == 1 or len(country_capital) == 0:
        results.append({
            'city': country_cities['city'].values[0],
            'country': country,
            'closer_capitals_count': 0,
            'closer_capitals': [],
            'own_capital_distance': 0
        })
        return results[0]

    for index, city in country_cities.iterrows():
        city_capitals_distances = []
        own_capital_distance = haversine(city['lng'], city['lat'], country_capital.iloc[0]['lng'], country_capital.iloc[0]['lat'])

        for cap_index, capital in capitals.iterrows():
            if capital['country'] != country:  # Exclude own country's capital
                distance = haversine(city['lng'], city['lat'], capital['lng'], capital['lat'])
                city_capitals_distances.append((capital['city'], distance, capital['country']))

        # Count foreign capitals closer than the own capital
        closer_capitals = [(cap[0], cap[1], cap[2]) for cap in city_capitals_distances if cap[1] < own_capital_distance]
        closer_capitals.sort(key=lambda x: x[1])

        results.append({
            'city': city['city'],
            'country': country,
            'closer_capitals_count': len(closer_capitals),
            'closer_capitals': closer_capitals,
            'own_capital_distance': own_capital_distance
        })

    # Find the city with the maximum number of closer foreign capitals
    most_closer_capitals_city = max(results, key=lambda x: x['closer_capitals_count'])
    return most_closer_capitals_city


# Function to get closer foreign capitals
def get_closer_foreign_capitals(city, country, file_path):
    # Load the data
    world_cities = pd.read_csv(file_path)
    if 'country' not in world_cities.columns:
        raise KeyError("The column 'country' is not found in the data.")

    capitals = world_cities[world_cities['capital'] == 'primary'][['city', 'lat', 'lng', 'country']]
    capitals = capitals.drop_duplicates(subset=['country'])
    # Find the specific city and the capital of the country
    specific_city = world_cities[(world_cities['country'] == country) & (world_cities['city'] == city)].iloc[0]
    own_capital = capitals[capitals['country'] == country].iloc[0]
    # Calculate the distance from the specific city to its own capital
    own_capital_distance = haversine(specific_city['lng'], specific_city['lat'], own_capital['lng'], own_capital['lat'])

    # Initialize an empty list to store closer foreign capitals
    closer_capitals = []

    # Calculate distances to all foreign capitals and filter
    for index, capital in capitals.iterrows():
        if capital['country'] != country:
            distance = haversine(specific_city['lng'], specific_city['lat'], capital['lng'], capital['lat'])
            if distance < own_capital_distance:
                closer_capitals.append((capital['city'], distance, capital['country']))

    # Sort capitals by distance
    closer_capitals.sort(key=lambda x: x[1])

    # Prepare the result in the requested format
    result = {
        'city': city,
        'country': country,
        'closer_capitals_count': len(closer_capitals),
        'closer_capitals': closer_capitals,
        'own_capital_distance': own_capital_distance
    }

    return result

# Function to display capital information
def display_capital_info(capital_data):
    st.write(f"**City:** {capital_data['city']}")
    st.write(f"**Country:** {capital_data['country']}")
    st.write(f"**Latitude:** {capital_data['lat']}")
    st.write(f"**Longitude:** {capital_data['lng']}")
    st.write(f"**Population:** {capital_data['population']}")
    st.map(pd.DataFrame({
        'lat': [capital_data['lat']],
        'lon': [capital_data['lng']]
    }))

# Function to create map with arcs
def create_map_with_arcs(city_data, file_path):
    world_cities = pd.read_csv(file_path)
    capitals = world_cities[world_cities['capital'] == 'primary'][['city', 'lat', 'lng', 'country']]
    capitals = capitals.drop_duplicates(subset=['country'])

    # Extract target city information
    target_city = world_cities[(world_cities['city'] == city_data['city']) & 
                               (world_cities['country'] == city_data['country'])]

    if target_city.empty:
        st.write("Target city not found!")  # Debugging
        return None
    else:
        target_city = target_city.iloc[0]
        st.write("Target city:", target_city)  # Debugging

    own_capital = capitals[capitals['country'] == city_data['country']].iloc[0]

    city_map = folium.Map(location=[target_city['lat'], target_city['lng']], zoom_start=5)
    folium.Marker([target_city['lat'], target_city['lng']],
                  popup=f"{city_data['city']} (Own City, {len(city_data['closer_capitals'])} closer capitals)",
                  icon=folium.Icon(color='green')).add_to(city_map)
    folium.Marker([own_capital['lat'], own_capital['lng']],
                  popup=f"{own_capital['city']} (Own Capital, {haversine(target_city['lng'], target_city['lat'], own_capital['lng'], own_capital['lat']): .2f} km)",
                  icon=folium.Icon(color='red')).add_to(city_map)
    folium.PolyLine(locations=[[target_city['lat'], target_city['lng']],
                               [own_capital['lat'], own_capital['lng']]],
                    color="red", weight=2, tooltip=f"{haversine(target_city['lng'], target_city['lat'], own_capital['lng'], own_capital['lat']): .2f} km").add_to(city_map)
    for capital in city_data['closer_capitals']:
        cap_info = capitals[(capitals['city'] == capital[0]) & (capitals['country'] == capital[2])]
        if not cap_info.empty:
            cap_info = cap_info.iloc[0]
            folium.PolyLine(locations=[[target_city['lat'], target_city['lng']],
                                       [cap_info['lat'], cap_info['lng']]],
                            color="blue", weight=2, tooltip=f"{capital[0]}: {capital[1]:.2f} km").add_to(city_map)
    return city_map

# Main function
def main():
    st.title('World Capitals Information')

    menu = ['Home', 'View Capitals', 'Stored Countries', 'City with Most Closer Capitals', 'About']
    choice = st.sidebar.selectbox('Menu', menu)

    df = load_data()

    if choice == 'Home':
        st.subheader('Home')
        st.write('Welcome to the World Capitals Information App!')
        
    elif choice == 'View Capitals':
        st.subheader('View Specific City')
        country = st.text_input('Enter country name')
        if country:
            result = df[df['country'].str.contains(country, case=False)]
            if not result.empty:
                selected_city = st.selectbox('Select a city', result['city'])
                if selected_city:
                    city_data = get_closer_foreign_capitals(selected_city, country, 'resources/worldcities.csv')
                    # st.write(f"City: {city_data['city']} ({city_data['closer_capitals_count']} closer capitals)")
                    city_map = create_map_with_arcs(city_data, 'resources/worldcities.csv')
                    if city_map:
                        folium_static(city_map)
                    st.dataframe(city_data['closer_capitals'], column_config={
                        "0": "City",
                        "1": "Distance",
                        "2": "Country"})
            else:
                st.write('No capitals found for the given country.')

    elif choice == 'Stored Countries':
        st.subheader('Stored Countries')
        stored_countries = df['country'].unique()
        st.write(stored_countries)
    
    elif choice == 'City with Most Closer Capitals':
        st.subheader('City with Most Closer Capitals')
        country = st.text_input('Enter country name', value="Germany")
        if country:
            result = df[df['country'].str.contains(country, case=False)]
        if not result.empty:
            country = st.selectbox('Select a country', result['country'].unique())
            city_data = find_city_with_most_closer_capitals(country, 'resources/worldcities.csv')
            st.write(f"City: {city_data['city']} ({city_data['closer_capitals_count']} closer capitals)")
            city_map = create_map_with_arcs(city_data, 'resources/worldcities.csv')
            if city_map:
                folium_static(city_map)
            st.dataframe(city_data['closer_capitals'], column_config={
                "0": "City",
                "1": "Distance",
                "2": "Country"})

    elif choice == 'About':
        st.subheader('About')
        st.write('This app provides information about world capitals.')

if __name__ == '__main__':
    main()
