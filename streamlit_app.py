import streamlit as st
import requests
from transformers import pipeline

# Page Configuration
st.set_page_config(page_title="🌿 Plant Assistant", layout="centered")
st.title("🌿 Plant Assistant")
st.markdown("Identify plants, detect diseases, and get care advice.")

# Model Loading
@st.cache_resource
def load_models():
    try:
        plant_model = pipeline("image-classification", model="microsoft/resnet-50")
        return plant_model, None
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None

plant_classifier, _ = load_models()

# --- Helper Functions (copied from your app.py) ---
def get_weather(city):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    try:
        geo_response = requests.get(geo_url)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        if not geo_data.get("results"):
            return {"error": f"City '{city}' not found."}
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        city_name = geo_data["results"][0]["name"]
        weather_params = {"latitude": lat, "longitude": lon, "current_weather": "true", "timezone": "auto"}
        weather_response = requests.get("https://api.open-meteo.com/v1/forecast", params=weather_params)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        current = weather_data.get("current_weather", {})
        temp = current.get("temperature")
        weather_code = current.get("weathercode")
        if weather_code == 0:
            weather_desc = "Clear"
        elif 1 <= weather_code <= 3:
            weather_desc = "Cloudy"
        elif 51 <= weather_code <= 67:
            weather_desc = "Rain"
        elif weather_code in (71, 73, 75):
            weather_desc = "Snow"
        else:
            weather_desc = "Unknown"
        return {"city": city_name, "temperature": temp, "weather": weather_desc}
    except Exception:
        return {"error": "Could not fetch weather"}

def generate_advice(plant_name, weather_info):
    clean_name = plant_name.replace('_', ' ').title()
    advice = f"**🌿 Plant:** {clean_name}\n\n"
    if "error" in weather_info:
        advice += "**💧 Tip:** Water when top inch of soil is dry."
        return advice
    temp = weather_info.get("temperature")
    weather_desc = weather_info.get("weather", "Unknown")
    city = weather_info.get("city", "your area")
    advice += f"**📍 Weather in {city}:** {weather_desc}, {temp}°C\n\n"
    if "Rain" in weather_desc:
        advice += "**🌧️ Tip:** Skip watering today!"
    elif temp is not None and temp > 30:
        advice += "**☀️ Tip:** Hot! Check soil, may need extra water."
    elif temp is not None and temp < 5:
        advice += "**❄️ Tip:** Cold! Bring indoors if outside."
    else:
        advice += "**💧 Tip:** Water when top inch of soil is dry."
    return advice

# --- Streamlit UI ---
tab1, tab2 = st.tabs(["🌱 Identify Plant", "🩺 Detect Disease"])

with tab1:
    uploaded_file = st.file_uploader("Upload a photo of your plant", type=["jpg", "jpeg", "png"])
    city = st.text_input("Enter your city for weather advice", placeholder="e.g., London")
    
    if uploaded_file is not None and city:
        if st.button("Identify Plant"):
            with st.spinner("Analyzing..."):
                if plant_classifier:
                    try:
                        image = Image.open(uploaded_file)
                        predictions = plant_classifier(image)
                        top = predictions[0]
                        weather = get_weather(city)
                        advice = generate_advice(top['label'], weather)
                        st.markdown(advice)
                        st.caption(f"Confidence: {top['score']:.2f}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Model not loaded.")

with tab2:
    st.info("Disease detection feature coming soon!")