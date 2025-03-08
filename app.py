import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from math import radians, sin, cos, sqrt, atan2
import sqlite3
import json


# Database functions
def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table(conn):
    """Create a table for storing request data."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        country TEXT NOT NULL,
        data TEXT NOT NULL
    );
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


def insert_request(conn, city, country, data):
    """Insert a new request into the requests table."""
    sql = '''INSERT INTO requests(city, country, data) VALUES(?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (city, country, data))
    conn.commit()
    return cur.lastrowid


def get_request(conn, city, country):
    """Query request data by city and country."""
    cur = conn.cursor()
    cur.execute("SELECT data FROM requests WHERE city=? AND country=?", (city, country))
    rows = cur.fetchall()
    if rows:
        return rows[0][0]
    return None


def list_table(conn, table):
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + table)
    rows = cur.fetchall()
    return rows


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
def find_city_with_most_closer_capitals(country, file_path, conn):
    # Check if data exists in the database
    cached_data = get_request(conn, "ALL_CITIES", country)
    if cached_data:
        return json.loads(cached_data)

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

    # Save to database
    insert_request(conn, "ALL_CITIES", country, json.dumps(most_closer_capitals_city))

    return most_closer_capitals_city


# Function to get closer foreign capitals
def get_closer_foreign_capitals(city, country, file_path, conn):
    # Check if data exists in the database
    cached_data = get_request(conn, city, country)
    if cached_data:
        return json.loads(cached_data)

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

    # Save to database
    insert_request(conn, city, country, json.dumps(result))

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
                  icon=folium.Icon(color='blue')).add_to(city_map)
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
            folium.Marker([cap_info['lat'], cap_info['lng']],
                  popup=f"{cap_info['city']}, {cap_info['country']} ({capital[1]:.2f} km)",
                  icon=folium.Icon(color='green')).add_to(city_map)
            folium.PolyLine(locations=[[target_city['lat'], target_city['lng']],
                                       [cap_info['lat'], cap_info['lng']]],
                            color="blue", weight=2, tooltip=f"{capital[0]}: {capital[1]:.2f} km").add_to(city_map)
    return city_map


# Main function
def main():
    st.title('World Capitals Information')

    database = "resources/requests.db"
    conn = create_connection(database)
    create_table(conn)

    menu = ['Home', 'View Capitals', 'City with Most Closer Capitals', 'Stored Countries', 'About']
    choice = st.sidebar.selectbox('Menu', menu)

    df = load_data()

    if choice == 'Home':
        st.subheader('Closer Capitals Streamlit App')
        st.image('resources/image.png', caption='Explore Global Capitals', use_column_width=True)
        st.markdown("""
        Explore global capitals and uncover unique geographic insights with the **Closer Capitals Streamlit App**. This app allows users to perform two fascinating analyses:
        1. **Find Closer Foreign Capitals**: For a selected city in any country, the app identifies all foreign capitals that are geographically closer to that city than its own national capital. This provides a surprising look at how proximity to foreign capitals can vary from expected distances.
        2. **Find the City with the Most Nearby Foreign Capitals**: For a selected country, the app identifies the city that has the highest number of foreign capitals closer to it than its own national capital. This reveals which city is geographically most surrounded by foreign capitals.
        **Disclaimer**: The results are based on the data from the `worldcities.csv` file used in the app. The accuracy of the results depends on the completeness and correctness of this dataset.
        Perfect for geography enthusiasts, educators, and anyone curious about the spatial relationships between world capitals.
        """)

    elif choice == 'View Capitals':
        st.subheader('View Specific City')
        countries = sorted(df['country'].unique())  # Get the unique list of countries from the data
        country = st.selectbox('Select a country', countries)  # Use a selectbox to show all countries
        if country:
            result = df[df['country'].str.contains(country, case=False)]
            if not result.empty:
                selected_city = st.selectbox('Select a city', sorted(result['city']))
                if selected_city:
                    city_data = get_closer_foreign_capitals(selected_city, country, 'resources/worldcities.csv', conn=conn)
                    st.write(f"City: {city_data['city']} ({city_data['closer_capitals_count']} closer capitals)")
                    city_map = create_map_with_arcs(city_data, 'resources/worldcities.csv')
                    if city_map:
                        folium_static(city_map)
                    st.dataframe(city_data['closer_capitals'], column_config={
                        "0": "City",
                        "1": "Distance",
                        "2": "Country"})
            else:
                st.write('No capitals found for the given country.')

    elif choice == 'City with Most Closer Capitals':
        st.subheader('City with Most Closer Capitals')
        countries = sorted(df['country'].unique())  # Get the unique list of countries from the data
        country = st.selectbox('Select a country', countries)  # Use a selectbox to show all countries
        if country:
            result = df[df['country'].str.contains(country, case=False)]
        if not result.empty:
            country = st.selectbox('Select a country', result['country'].unique())
            city_data = find_city_with_most_closer_capitals(country, 'resources/worldcities.csv', conn=conn)
            st.write(f"City: {city_data['city']} ({city_data['closer_capitals_count']} closer capitals)")
            city_map = create_map_with_arcs(city_data, 'resources/worldcities.csv')
            if city_map:
                folium_static(city_map)
            st.dataframe(city_data['closer_capitals'], column_config={
                "0": "City",
                "1": "Distance",
                "2": "Country"})
            
    elif choice == 'Stored Countries':
        st.subheader('Stored Countries')
        rows = list_table(conn, "requests")
        data = json.dumps(rows)
        frame = pd.read_json(data)
        st.table(frame)

    elif choice == 'About':
        st.subheader('About')

        st.markdown("""
        **Disclaimer**: 
        This app is a fun project and comes with absolutely no warranty—none, zero, zilch! 😄 
        If it gives you unexpected results, that's just part of the charm. 

        Think of it as a treasure hunt for capitals! 🗺️

        While we’ve done our best to make sure everything works, there may be bugs hiding out in the code. But hey, bugs are just extra features, right? 🐞

        If you have any suggestions, ideas, or just want to say hi, feel free to send them over. We love hearing from curious explorers like you! 🌍

        Now go ahead and dive into the world of capitals! 🚀
        """)


if __name__ == '__main__':
    main()
