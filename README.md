
# Closer Capitals Streamlit App

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
   git clone https://github.com/nrebel/closer-capitals-streamlit.git
   cd closer-capitals-streamlit
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

## Running the App with Docker

You can also run the app in a Docker container for a more isolated and reproducible environment.

### Docker Prerequisites

- **Docker**: Make sure Docker is installed on your machine. You can download and install Docker from [here](https://www.docker.com/products/docker-desktop).

### Docker Instructions

1. **Create a `Dockerfile`** in the root of the project (or use the one provided):

   ```Dockerfile
   # Base image
   FROM python:3.9-slim

   # Set the working directory
   WORKDIR /app

   # Create a non-root user and group
   RUN groupadd -r appuser && useradd -r -g appuser appuser

   # Copy the requirements file and install dependencies
   COPY requirements.txt .

   RUN pip install --no-cache-dir -r requirements.txt

   # Copy the entire application code into the container
   COPY . .

   # Change ownership of the application files to the non-root user
   RUN chown -R appuser:appuser /app

   # Switch to the non-root user
   USER appuser

   # Expose port 8501 for Streamlit
   EXPOSE 8501

   # Command to run the app
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Create a `requirements.txt` file** if it doesn’t already exist. It should contain the necessary dependencies:

   ```txt
   streamlit
   pandas
   folium
   streamlit-folium
   sqlite3
   ```

3. **Build the Docker image**:
   In the root of the project, run the following command to build the Docker image:
   
   ```bash
   docker build -t closer-capitals-streamlit .
   ```

4. **Run the Docker container**:
   After the image is built, you can run the app in a container:
   
   ```bash
   docker run -p 8501:8501 closer-capitals-streamlit
   ```

5. **Access the app**:
   Open your browser and go to `http://localhost:8501` to access the Streamlit app running inside Docker.

### Database Persistence in Docker

If you want the SQLite database to persist across container restarts, you can mount a volume to store the database file. Use the following command to mount a volume:

```bash
docker run -p 8501:8501 -v $(pwd)/resources:/app/resources closer-capitals-streamlit
```

This ensures that the `resources` directory in the container is mapped to the `resources` directory on your local machine, allowing the database to persist.

## Contributing

Feel free to contribute to this project by submitting issues or pull requests. Any suggestions or improvements are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
