
# World Capitals Information App

This Streamlit app provides detailed information about world capitals, allowing users to explore cities, find foreign capitals closer to their city than their own capital, and analyze stored requests. The app uses a local SQLite database to store data and features dynamic maps created with Folium.

## Features

- **Home**: Welcome screen introducing the user to the application.
- **View Capitals**: Find foreign capitals that are closer to a selected city than its own capital.
- **Stored Countries**: View a list of all previously queried countries and cities stored in the local SQLite database.
- **City with Most Closer Capitals**: Identify the city in a selected country that has the most foreign capitals closer than its own capital.
- **About**: Information about the app.

## Getting Started

### Prerequisites

To run this app, you'll need the following:

- **Python 3.x**
- **Streamlit**: Install using `pip install streamlit`
- **Pandas**: Install using `pip install pandas`
- **Folium**: Install using `pip install folium`
- **Streamlit-Folium**: Install using `pip install streamlit-folium`

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repository/world-capitals-app.git
   cd world-capitals-app
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Prepare the necessary resources:
   - Ensure the `resources/requests.db` SQLite database is present. If it's not, the app will create it.
   - Ensure the `resources/worldcities.csv` file is present with the correct city data, including latitude, longitude, and capital information.

### Running the App

To start the app, run the following command:
```bash
streamlit run app.py
```

### Database Schema

The app uses a local SQLite database (`resources/requests.db`) to store data from user requests:

- **requests**: Stores the city, country, and query results in JSON format.
  - `id` (INTEGER): Primary key.
  - `city` (TEXT): The city that was queried.
  - `country` (TEXT): The country of the city.
  - `data` (TEXT): JSON data storing the results of the query.

### Data Caching

The app caches the loaded city data using Streamlit’s caching mechanism to improve performance and avoid redundant database queries.

## App Functionality

### Haversine Formula

The app uses the Haversine formula to calculate the great-circle distance between two points on the Earth (specified in latitude and longitude). This is used to compute the distances between cities and capitals.

### Database Storage

The app stores the results of queries to avoid redundant calculations. If the same query is made, the app will retrieve the result from the SQLite database rather than recalculating it.

### Maps with Folium

The app generates interactive maps with Folium, displaying the selected city, its own capital, and foreign capitals that are closer than the city's own capital. The distances between the cities are shown on the map as lines.

## Contributing

Feel free to contribute to this project by submitting issues or pull requests. Any suggestions or improvements are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
