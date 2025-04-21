import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime
import pydeck as pdk

# ============ API and Configuration ============ 
WEATHERAPI_KEY = "d11086cbdc19454fb40123138251904"
WEATHERAPI_URL = "http://api.weatherapi.com/v1/forecast.json"

st.set_page_config(page_title="🌤️ Weather App", layout="wide")

# ============ Styling ============ 
st.markdown("""
    <style>
        body {
            background-color: #f4f6f8;
        }
        .weather-box {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
            font-family: 'Segoe UI', sans-serif;
        }
        .label {
            font-weight: 900;
            font-size: 20px;
            letter-spacing: 2px;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        .value {
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .temp { color: #e67300; }
        .cond { color: #0099cc; }
        .humid { color: #33cc33; }
        .wind { color: #6666ff; }
    </style>
""", unsafe_allow_html=True)

# ============ Sidebar ============ 
st.sidebar.title("🔍 SEARCH WEATHER")
city = st.sidebar.text_input("Enter place")
lat = st.sidebar.text_input("Latitude (optional)")
lon = st.sidebar.text_input("Longitude (optional)")
theme = st.sidebar.radio("Select Theme", ('Light', 'Dark'))
alerts = st.sidebar.checkbox("Set Weather Alerts (e.g., rain, snow)")

# Custom Alert Settings
alert_temp = st.sidebar.number_input("Alert if Temperature exceeds (°C)", min_value=-50, max_value=50, value=30)
alert_wind_speed = st.sidebar.number_input("Alert if Wind Speed exceeds (km/h)", min_value=0, max_value=200, value=50)
alert_rain = st.sidebar.checkbox("Alert if Rain is Detected")

if theme == 'Dark':
    st.markdown("""
    <style>
        body {
            background-color: #2c3e50;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("🌍 LIVE WEATHER DASHBOARD")
st.markdown("<div style='font-size: 20px; text-align: center; color: white;'>Get current weather data from anywhere in the world 🌎</div>", unsafe_allow_html=True)

# ============ API Functions ============ 
def get_weatherapi_forecast(query):
    url = f"{WEATHERAPI_URL}?key={WEATHERAPI_KEY}&q={query}&days=7&aqi=no&alerts=yes"
    return requests.get(url).json()

def get_coordinates_from_place(place_name):
    try:
        if len(place_name.split()) == 1:
            place_name += ", Himachal Pradesh"
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place_name, "format": "json"},
            headers={"User-Agent": "weather-app-streamlit"}
        )
        results = response.json()
        if results:
            return results[0]["lat"], results[0]["lon"]
        else:
            return None, None
    except Exception:
        return None, None

# ============ Main Code ============ 
if st.sidebar.button("Get Weather"):
    if not city and not (lat and lon):
        st.error("Please enter a valid city name or coordinates.")
    else:
        if lat and lon:
            query = f"{lat},{lon}"
        else:
            test_data = get_weatherapi_forecast(city)
            if "error" in test_data:
                st.warning("City not recognized. Trying to fetch coordinates using geocoding...")
                lat_found, lon_found = get_coordinates_from_place(city)
                if lat_found and lon_found:
                    query = f"{lat_found},{lon_found}"
                else:
                    st.error("❌ Location not found. Try using coordinates instead.")
                    st.stop()
            else:
                query = city

        data = get_weatherapi_forecast(query)

        if "current" in data:
            current = data["current"]
            location = data["location"]
            forecast = data["forecast"]["forecastday"]

            # Get the current weather data
            temp = current["temp_c"]
            wind_speed = current["wind_kph"]
            weather_condition = current["condition"]["text"]
            rain = "rain" in weather_condition.lower()

            # Check if custom alert conditions are met
            alert_message = ""
            if temp > alert_temp:
                alert_message += f"🚨 Temperature Alert: {temp}°C is above {alert_temp}°C!<br>"
            if wind_speed > alert_wind_speed:
                alert_message += f"🚨 Wind Speed Alert: {wind_speed} km/h is above {alert_wind_speed} km/h!<br>"
            if alert_rain and rain:
                alert_message += "🚨 Rain Alert: Rain detected in the current weather conditions!<br>"

            if alert_message:
                st.markdown(f"<div style='padding:10px; background-color:#000000; border-left:6px solid red; margin-bottom:10px; border-radius:8px;'>{alert_message}</div>", unsafe_allow_html=True)

                if alerts:  # Play alert sound if user has selected it
                    st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3", autoplay=True)

            else:
                st.info("No custom alerts triggered.")

            # Displaying current weather data
            weather = current["condition"]["text"]
            icon_url = "https:" + current["condition"]["icon"]
            sunrise = forecast[0]["astro"]["sunrise"]
            sunset = forecast[0]["astro"]["sunset"]

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="weather-box">', unsafe_allow_html=True)
                st.image(icon_url, width=100)
                st.markdown(f"### 📍 {location['name']}, {location['country']}")
                st.markdown(f"<div class='label cond'>CONDITION:</div><div class='value cond'>{weather}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='label temp'>🌡️ TEMPERATURE:</div><div class='value temp'>{temp} °C</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='label humid'>💧 HUMIDITY:</div><div class='value humid'>{current['humidity']}%</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='label wind'>💨 WIND SPEED:</div><div class='value wind'>{wind_speed} km/h</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='label'>🌅 SUNRISE:</div><div class='value'>{sunrise}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='label'>🌇 SUNSET:</div><div class='value'>{sunset}</div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ========= 7-Day Forecast =========
            def condition_to_emoji(cond):
                cond = cond.lower()
                if "sun" in cond or "clear" in cond:
                    return "☀️"
                elif "cloud" in cond:
                    return "☁️"
                elif "rain" in cond:
                    return "🌧️"
                elif "thunder" in cond:
                    return "⛈️"
                elif "snow" in cond:
                    return "❄️"
                elif "fog" in cond or "mist" in cond:
                    return "🌫️"
                else:
                    return "🌈"

            days = [datetime.strptime(d["date"], '%Y-%m-%d').strftime('%A') for d in forecast]
            dates = [d["date"] for d in forecast]
            temps = [d["day"]["avgtemp_c"] for d in forecast]
            conditions = [d["day"]["condition"]["text"] for d in forecast]
            emojis = [condition_to_emoji(c) for c in conditions]

            fig = go.Figure(data=[go.Bar(
                x=[f"{d} ({day}) {e}" for d, day, e in zip(dates, days, emojis)],
                y=temps,
                marker=dict(color='rgba(0, 191, 255, 0.6)'),
                text=conditions
            )])
            fig.update_layout(title=f"7-Day Weather Forecast for {location['name']}",
                              xaxis_title="Day",
                              yaxis_title="Avg Temp (°C)")
            st.plotly_chart(fig)

            # ========= 12-Hour Forecast =========
            st.subheader("🕒 12-Hour Forecast ")

            hourly_data = forecast[0]["hour"]
            current_hour = datetime.now().hour
            next_12_hours = hourly_data[current_hour:current_hour + 12]

            hour_labels = []
            hour_temps = []
            hour_emojis = []
            hour_conditions = []

            for hour in next_12_hours:
                time_obj = datetime.strptime(hour["time"], '%Y-%m-%d %H:%M')
                hour_labels.append(time_obj.strftime('%I %p'))
                hour_temps.append(hour["temp_c"])
                hour_emojis.append(condition_to_emoji(hour["condition"]["text"]))
                hour_conditions.append(hour["condition"]["text"])

            custom_labels = [
                f"<b>{label}</b><br>{cond}<br>{emoji}" 
                for label, cond, emoji in zip(hour_labels, hour_conditions, hour_emojis)
            ]

            fig12 = go.Figure(data=[go.Bar(
                x=hour_labels,
                y=hour_temps,
                text=custom_labels,
                hoverinfo="text",
                marker=dict(color='rgba(255, 165, 0, 0.7)'),
            )])

            fig12.update_layout(
                title="12-Hour Temperature Forecast",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                xaxis=dict(tickmode='linear'),
                margin=dict(t=40, b=40)
            )

            st.plotly_chart(fig12)

            # ========= 3D Map =========
            st.subheader("🌍 3D Map of Your Location")

            # Use coordinates from the API or input coordinates
            latitude = float(lat) if lat else data["location"]["lat"]
            longitude = float(lon) if lon else data["location"]["lon"]

            location = pdk.Deck(
                initial_view_state=pdk.ViewState(
                    latitude=latitude,
                    longitude=longitude,
                    zoom=10,
                    pitch=45  # 3D perspective
                ),
                layers=[pdk.Layer(
                    'ScatterplotLayer',
                    data=[{'lat': latitude, 'lon': longitude, 'size': 100}],
                    get_position='[lon, lat]',
                    get_radius=10000,
                    get_fill_color='[255, 0, 0]',
                    pickable=True
                )]
            )
            st.pydeck_chart(location)
        else:
            st.error("❌ City not found or API limit reached. Please try again or check your API key.")