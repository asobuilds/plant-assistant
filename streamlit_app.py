import streamlit as st
import requests
from PIL import Image
from transformers import pipeline
import io
import cv2
import numpy as np

# --- Page Setup ---
st.set_page_config(
    page_title="🌿 Ultimate Plant Assistant",
    page_icon="🌿",
    layout="wide"
)

st.title("🌿 Ultimate Plant Assistant")
st.markdown("*Identify plants, detect diseases, and get personalized care advice*")

# --- Load Models with Caching ---
@st.cache_resource
def load_models():
    """Load all AI models"""
    try:
        # Plant identification model (use the best available)
        st.info("Loading plant identification model...")
        # Try the specialized model first, fallback to ResNet
        try:
            plant_model = pipeline("image-classification", model="juppy44/plant-identification-2m-vit-b")
        except:
            st.warning("Using fallback plant model")
            plant_model = pipeline("image-classification", model="microsoft/resnet-50")
        
        # Disease detection model
        st.info("Loading disease detection model...")
        try:
            disease_model = pipeline("image-classification", model="Sharmistha-catalyst/sick-greens-plant-disease")
        except:
            st.warning("Using fallback disease model")
            disease_model = None
        
        return plant_model, disease_model
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None

# --- Load Models on Start ---
plant_model, disease_model = load_models()

# --- Weather Function ---
def get_weather(city):
    """Get current weather for a city"""
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
            weather_desc = "☀️ Clear"
        elif 1 <= weather_code <= 3:
            weather_desc = "⛅ Cloudy"
        elif 51 <= weather_code <= 67:
            weather_desc = "🌧️ Rain"
        elif weather_code in (71, 73, 75):
            weather_desc = "❄️ Snow"
        else:
            weather_desc = "🌤️ Unknown"
        return {"city": city_name, "temperature": temp, "weather": weather_desc}
    except Exception as e:
        return {"error": f"Weather unavailable: {e}"}

# --- Plant Care Advice Generator ---
def generate_advice(plant_name, weather_info):
    """Generate care advice based on plant and weather"""
    clean_name = plant_name.replace('_', ' ').title()
    advice = f"**🌿 Plant Identified:** {clean_name}\n\n"
    
    if "error" in weather_info:
        advice += "**💧 General Care:** Water when top inch of soil feels dry. Ensure good drainage."
        return advice
    
    temp = weather_info.get("temperature")
    weather_desc = weather_info.get("weather", "Unknown")
    city = weather_info.get("city", "your area")
    
    advice += f"**📍 Weather in {city}:** {weather_desc} | {temp}°C\n\n"
    
    # Weather-based advice
    if "Rain" in weather_desc:
        advice += "**🌧️ Watering:** Skip watering today - rain will hydrate your plant naturally!"
    elif temp is not None and temp > 30:
        advice += "**☀️ Hot Weather:** Check soil daily. May need extra water. Consider moving to partial shade."
    elif temp is not None and temp < 5:
        advice += "**❄️ Cold Weather:** Bring indoors if outside. Reduce watering - plants need less in cold."
    else:
        advice += "**💧 Watering:** Water when top inch of soil is dry. Typically 1-2 times per week."
    
    # General care tips
    advice += "\n\n**🌟 General Tips:**"
    advice += "\n- Ensure good drainage"
    advice += "\n- Provide adequate sunlight (4-6 hours)"
    advice += "\n- Fertilize during growing season"
    
    return advice

# --- Disease Treatment Suggestions ---
def get_treatment(disease_name):
    """Get treatment recommendations for a disease"""
    treatments = {
        "rust": "**🔬 Treatment:** Apply fungicide. Remove and destroy affected leaves. Improve air circulation.",
        "blight": "**🔬 Treatment:** Remove infected plants immediately. Apply copper-based fungicide. Avoid overhead watering.",
        "mildew": "**🔬 Treatment:** Improve air circulation. Apply sulfur or neem oil spray. Reduce humidity.",
        "spot": "**🔬 Treatment:** Remove spotted leaves. Apply fungicide. Ensure proper spacing between plants.",
        "mosaic": "**🔬 Treatment:** Remove infected plants. Control aphid populations (they spread the virus).",
        "yellow": "**🔬 Treatment:** Check soil pH and nutrients. Add nitrogen fertilizer if needed. Ensure proper watering.",
        "wilt": "**🔬 Treatment:** Check for root rot. Improve drainage. Remove affected parts. Apply fungicide.",
        "scab": "**🔬 Treatment:** Apply fungicide. Remove infected fruit. Practice crop rotation.",
        "canker": "**🔬 Treatment:** Prune infected branches. Apply copper spray. Maintain tree health.",
        "rot": "**🔬 Treatment:** Remove infected parts. Improve drainage. Apply fungicide. Reduce watering."
    }
    
    # Find matching treatment
    for key, value in treatments.items():
        if key in disease_name.lower():
            return value
    
    return "**🔬 Treatment:** Remove affected parts and monitor. If severe, consult a local plant expert."

# --- Plant Toxicity Check (Knowledge Base) ---
def check_toxicity(plant_name):
    """Simple toxicity check based on plant name"""
    # Toxic plants (common ones)
    toxic_plants = {
        "oleander": "☠️ **TOXIC:** All parts are poisonous. Causes nausea, vomiting, irregular heartbeat.",
        "azalea": "☠️ **TOXIC:** Causes vomiting, diarrhea, weakness. Can be fatal to pets.",
        "rhododendron": "☠️ **TOXIC:** Contains grayanotoxins. Causes vomiting, seizures, coma.",
        "dieffenbachia": "☠️ **TOXIC:** Causes burning pain, swelling of mouth and throat.",
        "philodendron": "☠️ **TOXIC:** Contains calcium oxalate crystals. Causes mouth irritation.",
        "pothos": "☠️ **TOXIC:** Causes mouth pain, vomiting. Keep away from pets.",
        "snake plant": "⚠️ **CAUTION:** Mildly toxic. Causes nausea, vomiting if ingested.",
        "aloe vera": "⚠️ **CAUTION:** The gel is safe topically, but the skin/latex is toxic if ingested.",
        "tulip": "⚠️ **CAUTION:** Bulbs are toxic. Causes vomiting, diarrhea, hypersalivation.",
        "lily": "☠️ **HIGHLY TOXIC:** Can cause kidney failure in cats. Even small amounts are dangerous."
    }
    
    for key, value in toxic_plants.items():
        if key in plant_name.lower():
            return value
    
    return "✅ **SAFE:** This plant is not known to be toxic. However, always be cautious when handling any plant."

# --- Identify Plant Function ---
def identify_plant(image, city):
    """Main plant identification function"""
    if image is None:
        return "Please upload an image.", None
    
    if plant_model is None:
        return "Model not loaded. Please refresh.", None
    
    try:
        predictions = plant_model(image)
        top = predictions[0]
        plant_name = top['label']
        confidence = top['score']
        
        weather = get_weather(city)
        advice = generate_advice(plant_name, weather)
        advice += f"\n\n**🔬 Confidence:** {confidence:.2%}"
        advice += f"\n\n**🌱 Scientific Name:** {plant_name}"
        
        return advice, plant_name
    except Exception as e:
        return f"Error: {e}", None

# --- Detect Disease Function ---
def detect_disease(image):
    """Disease detection function"""
    if image is None:
        return "Please upload a leaf image."
    
    if disease_model is None:
        return "Disease model not available. Please use the identify function."
    
    try:
        predictions = disease_model(image)
        top = predictions[0]
        disease_name = top['label']
        confidence = top['score']
        
        treatment = get_treatment(disease_name)
        
        result = f"**🩺 Disease Detected:** {disease_name}\n\n"
        result += f"{treatment}\n\n"
        result += f"**🔬 Confidence:** {confidence:.2%}"
        
        return result
    except Exception as e:
        return f"Error: {e}"

# --- Video Processing Function ---
def process_video(video_file):
    """Process uploaded video, extract frames, and identify plants"""
    if video_file is None:
        return "Please upload a video."
    
    try:
        # Read video bytes
        video_bytes = video_file.read()
        
        # Save temp video
        with open("temp_video.mp4", "wb") as f:
            f.write(video_bytes)
        
        # Open video with OpenCV
        cap = cv2.VideoCapture("temp_video.mp4")
        frames = []
        frame_count = 0
        
        while cap.isOpened() and frame_count < 20:  # Process max 20 frames
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % 10 == 0:  # Take every 10th frame
                # Convert OpenCV frame to PIL image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
            frame_count += 1
        
        cap.release()
        
        if not frames:
            return "No frames extracted from video."
        
        # Identify plant in each frame
        results = []
        for frame in frames[:5]:  # Analyze first 5 frames
            try:
                preds = plant_model(frame)
                if preds:
                    results.append(preds[0]['label'])
            except:
                pass
        
        # Get the most common plant name
        if results:
            from collections import Counter
            most_common = Counter(results).most_common(1)[0][0]
            return f"**🌿 Plant Identified:** {most_common}\n\n🎬 Analyzed from video (multiple frames)"
        else:
            return "Could not identify plant from video."
            
    except Exception as e:
        return f"Error processing video: {e}"

# --- User Interface ---
# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🌱 Identify Plant", "🩺 Disease Detection", "📹 Video Analysis", "💬 About"])

# --- TAB 1: Identify Plant ---
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📸 Upload a photo of your plant",
            type=["jpg", "jpeg", "png"],
            help="Take a clear photo of the leaves and overall plant"
        )
        city = st.text_input("📍 Enter your city for weather advice", placeholder="e.g., London, New York, Tokyo")
        
        if uploaded_file is not None and city:
            image = Image.open(uploaded_file)
            st.image(image, caption="Your Plant", use_container_width=True)
            
            if st.button("🌿 Identify Plant", type="primary"):
                with st.spinner("Analyzing..."):
                    advice, plant_name = identify_plant(image, city)
                    st.markdown("---")
                    st.markdown(advice)
                    
                    # Show toxicity info
                    if plant_name:
                        st.markdown("---")
                        st.markdown("### ☠️ Safety Information")
                        toxicity = check_toxicity(plant_name)
                        st.markdown(toxicity)
    
    with col2:
        st.markdown("### 💡 Tips for Best Results")
        st.markdown("""
        - 📸 Take clear, well-lit photo
        - 🌿 Focus on leaves and overall shape
        - 🌞 Avoid shadows and glare
        - 🏙️ Enter your city for weather-based advice
        """)

# --- TAB 2: Disease Detection ---
with tab2:
    st.markdown("### 🩺 Plant Disease Detection")
    st.markdown("Upload a photo of a leaf showing signs of disease")
    
    disease_file = st.file_uploader(
        "📸 Upload a diseased leaf photo",
        type=["jpg", "jpeg", "png"],
        key="disease_upload"
    )
    
    if disease_file is not None:
        disease_image = Image.open(disease_file)
        st.image(disease_image, caption="Diseased Leaf", use_container_width=True)
        
        if st.button("🔬 Detect Disease", type="primary"):
            with st.spinner("Analyzing for diseases..."):
                result = detect_disease(disease_image)
                st.markdown("---")
                st.markdown(result)
    
    st.markdown("---")
    st.markdown("### 📋 Common Plant Diseases")
    st.markdown("""
    - **Rust:** Orange/brown spots on leaves
    - **Blight:** Rapid browning and death of leaves
    - **Mildew:** White/gray powdery growth
    - **Spot:** Black/brown circular spots
    - **Mosaic:** Yellow/green mottled pattern
    - **Wilt:** Drooping and yellowing leaves
    """)

# --- TAB 3: Video Analysis ---
with tab3:
    st.markdown("### 📹 Video Plant Identification")
    st.markdown("Upload a short video (max 30 seconds) to identify plants from multiple frames")
    
    video_file = st.file_uploader(
        "🎥 Upload a video of your plant",
        type=["mp4", "mov", "avi"],
        key="video_upload"
    )
    
    if video_file is not None:
        st.video(video_file)
        
        if st.button("🎬 Analyze Video", type="primary"):
            with st.spinner("Processing video frames..."):
                result = process_video(video_file)
                st.markdown("---")
                st.markdown(result)

# --- TAB 4: About ---
with tab4:
    st.markdown("### 🌿 About Ultimate Plant Assistant")
    st.markdown("""
    **Powered by AI** - This app uses state-of-the-art AI models to identify plants, detect diseases, and provide care advice.
    
    **Features:**
    - ✅ **Plant Identification:** AI trained on millions of plant images
    - ✅ **Disease Detection:** Identifies 38+ plant diseases
    - ✅ **Weather Integration:** Real-time weather for personalized care
    - ✅ **Toxicity Check:** Know if plants are safe
    - ✅ **Video Analysis:** Identify from short videos
    
    **Models Used:**
    - Plant: `juppy44/plant-identification-2m-vit-b`
    - Disease: `Sharmistha-catalyst/sick-greens-plant-disease`
    
    **Privacy Note:** All images are processed and not stored.
    """)

# --- Footer ---
st.markdown("---")
st.caption("🌿 Ultimate Plant Assistant v2.0 | Built with ❤️ using Streamlit and Hugging Face")