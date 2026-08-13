import os
# Set your Hugging Face token here (replace with your actual token)

import gradio as gr
import requests
from transformers import pipeline
from PIL import Image
import io

# --- Configuration ---
PLANT_MODEL_ID = "juppy44/plant-identification-2m-vit-b"
DISEASE_MODEL_ID = "Sharmistha-catalyst/sick-greens-plant-disease"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

# --- Load Models ---
print("Loading plant identification model...")
try:
    plant_classifier = pipeline("image-classification", model=PLANT_MODEL_ID)
    print("✅ Plant model loaded!")
except Exception as e:
    print(f"⚠️ Plant model failed: {e}")
    print("Using backup model...")
    plant_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

print("Loading disease detection model...")
try:
    disease_classifier = pipeline("image-classification", model=DISEASE_MODEL_ID)
    print("✅ Disease model loaded!")
except Exception as e:
    print(f"⚠️ Disease model failed: {e}")
    disease_classifier = None

# --- Weather Function ---
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
        weather_response = requests.get(WEATHER_API_URL, params=weather_params)
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
    except:
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

# --- Function 1: Identify Plant ---
def identify_plant(image, city):
    if image is None:
        return "Please upload an image."
    try:
        predictions = plant_classifier(image)
        top = predictions[0]
        plant_name = top['label']
        confidence = top['score']
        weather = get_weather(city)
        advice = generate_advice(plant_name, weather)
        advice += f"\n\n*(🔬 Confidence: {confidence:.2f})*"
        return advice
    except Exception as e:
        return f"Error: {e}"

# --- Function 2: Detect Disease ---
def detect_disease(image):
    if image is None:
        return "Please upload a leaf image."
    if disease_classifier is None:
        return "Disease model not available."
    try:
        predictions = disease_classifier(image)
        top = predictions[0]
        disease_name = top['label']
        confidence = top['score']
        treatments = {
            "rust": "Apply fungicide. Remove affected leaves.",
            "blight": "Remove infected plants. Use copper-based spray.",
            "mildew": "Improve air circulation. Apply sulfur spray.",
            "spot": "Remove spotted leaves. Apply fungicide.",
            "mosaic": "Remove infected plants. Control aphids.",
            "yellow": "Check soil nutrients. Add nitrogen fertilizer.",
            "wilt": "Check for root rot. Improve drainage.",
            "scab": "Apply fungicide. Remove infected fruit.",
            "canker": "Prune infected branches. Apply copper spray.",
            "rot": "Remove infected parts. Improve drainage."
        }
        treatment = "Remove affected parts and monitor."
        for key, value in treatments.items():
            if key in disease_name.lower():
                treatment = value
                break
        result = f"**🩺 Disease:** {disease_name}\n\n"
        result += f"**💊 Treatment:** {treatment}\n\n"
        result += f"*(🔬 Confidence: {confidence:.2f})*"
        return result
    except Exception as e:
        return f"Error: {e}"

# --- Create the Web Interface ---
with gr.Blocks(title="Plant Assistant") as demo:
    gr.Markdown("# 🌿 Ultimate Plant Assistant")
    gr.Markdown("Identify plants, detect diseases, and get care advice.")
    
    with gr.Tab("🌱 Identify Plant"):
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(type="pil", label="Upload Plant Photo")
                city_input = gr.Textbox(label="Enter Your City", placeholder="e.g., London")
                identify_btn = gr.Button("Identify Plant")
            with gr.Column():
                plant_output = gr.Markdown(label="Results")
        identify_btn.click(identify_plant, [image_input, city_input], plant_output)
    
    with gr.Tab("🩺 Detect Disease"):
        with gr.Row():
            with gr.Column():
                disease_image = gr.Image(type="pil", label="Upload Leaf with Disease")
                disease_btn = gr.Button("Detect Disease")
            with gr.Column():
                disease_output = gr.Markdown(label="Results")
        disease_btn.click(detect_disease, [disease_image], disease_output)
    
    with gr.Tab("📊 About"):
        gr.Markdown("""
        ### How It Works
        - **Identify Plant**: Uses AI trained on 2M+ plant images.
        - **Detect Disease**: Identifies 38 plant diseases and suggests treatments.
        - **Weather Advice**: Gives care tips based on your local weather.
        """)

# --- Launch the App ---
if __name__ == "__main__":
    demo.launch()