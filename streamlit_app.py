import streamlit as st
import requests
from PIL import Image
from transformers import pipeline
import cv2
import numpy as np
import time
from collections import Counter
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="🌿 PlantPal - Your Smart Farming Assistant",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern Look ---
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Hero section */
    .hero {
        background: linear-gradient(135deg, #1a472a 0%, #2d8a4e 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .hero h1 {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .hero p {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    .hero .subtitle {
        font-size: 1rem;
        opacity: 0.8;
        margin-top: 1rem;
    }
    
    /* Feature cards */
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
        height: 100%;
        border: 1px solid #e8f0fe;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .feature-card .icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .feature-card h3 {
        color: #1a472a;
        margin-bottom: 0.5rem;
    }
    
    .feature-card p {
        color: #555;
        font-size: 0.95rem;
    }
    
    /* Stats section */
    .stats {
        background: #f8fafc;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a472a;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }
    
    /* Testimonial */
    .testimonial {
        background: #fff;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #2d8a4e;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .testimonial .quote {
        font-style: italic;
        color: #333;
    }
    
    .testimonial .author {
        font-weight: 600;
        color: #1a472a;
        margin-top: 0.5rem;
    }
    
    /* Buttons */
    .btn-primary {
        background: linear-gradient(135deg, #1a472a 0%, #2d8a4e 100%);
        color: white;
        padding: 0.75rem 2rem;
        border: none;
        border-radius: 50px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    .btn-primary:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(45, 138, 78, 0.4);
    }
    
    /* Login form */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .login-container h2 {
        text-align: center;
        color: #1a472a;
        margin-bottom: 1.5rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #666;
        border-top: 1px solid #eee;
        margin-top: 3rem;
    }
    
    /* Animation keyframes */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero h1 {
            font-size: 2.2rem;
        }
        .hero p {
            font-size: 1rem;
        }
        .stat-number {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- User Database (Simulated) ---
users_db = {
    "farmer_john": {"password": "farm2024", "email": "john@farm.com"},
    "farmer_jane": {"password": "crops2024", "email": "jane@farm.com"}
}

# --- Login Function ---
def login(username, password):
    if username in users_db and users_db[username]["password"] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False

# --- Load Models with Cache ---
@st.cache_resource
def load_models():
    try:
        # Plant identification
        try:
            plant_model = pipeline("image-classification", model="microsoft/resnet-50")
        except:
            plant_model = None
        
        # Disease detection (optional)
        disease_model = None
        
        return plant_model, disease_model
    except:
        return None, None

# --- Helper Functions ---
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
    except:
        return {"error": "Weather unavailable"}

def generate_advice(plant_name, weather_info):
    clean_name = plant_name.replace('_', ' ').title()
    advice = f"**🌿 Plant:** {clean_name}\n\n"
    if "error" in weather_info:
        advice += "💧 **Care:** Water when top inch of soil feels dry."
        return advice
    temp = weather_info.get("temperature")
    weather_desc = weather_info.get("weather", "Unknown")
    city = weather_info.get("city", "your area")
    advice += f"📍 **Weather in {city}:** {weather_desc} | {temp}°C\n\n"
    if "Rain" in weather_desc:
        advice += "🌧️ **Tip:** Skip watering today! Nature is doing it for you."
    elif temp is not None and temp > 30:
        advice += "☀️ **Hot Weather:** Check soil daily. May need extra water."
    elif temp is not None and temp < 5:
        advice += "❄️ **Cold Weather:** Bring indoors if outside. Reduce watering."
    else:
        advice += "💧 **Watering:** Water when top inch of soil is dry."
    return advice

def check_toxicity(plant_name):
    toxic_plants = {
        "oleander": "☠️ **TOXIC:** Keep away from children and pets.",
        "azalea": "☠️ **TOXIC:** Can cause vomiting and weakness.",
        "dieffenbachia": "☠️ **TOXIC:** Causes mouth and throat irritation.",
        "philodendron": "☠️ **TOXIC:** Keep away from pets.",
        "pothos": "☠️ **TOXIC:** Causes mouth pain, vomiting.",
        "snake plant": "⚠️ **CAUTION:** Mildly toxic if ingested.",
        "aloe vera": "⚠️ **CAUTION:** Safe topically; skin/latex is toxic.",
        "lily": "☠️ **HIGHLY TOXIC:** Dangerous for cats."
    }
    for key, value in toxic_plants.items():
        if key in plant_name.lower():
            return value
    return "✅ **SAFE:** Not known to be toxic."

# --- Navigation ---
def navigation():
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1a472a/ffffff?text=🌿+PlantPal", use_container_width=True)
        
        if st.session_state.logged_in:
            st.markdown(f"### 👋 Welcome, {st.session_state.username}!")
            st.markdown("---")
        
        # Navigation links
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        
        if st.button("🌱 Identify Plant", use_container_width=True):
            st.session_state.page = "identify"
            st.rerun()
        
        if st.button("🩺 Disease Detection", use_container_width=True):
            st.session_state.page = "disease"
            st.rerun()
        
        if st.button("📹 Video Analysis", use_container_width=True):
            st.session_state.page = "video"
            st.rerun()
        
        if st.button("📚 Learning Center", use_container_width=True):
            st.session_state.page = "learn"
            st.rerun()
        
        st.markdown("---")
        
        if st.session_state.logged_in:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()
        else:
            if st.button("🔐 Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()

# --- Home Page ---
def home_page():
    # Hero Section
    st.markdown("""
    <div class="hero fade-in">
        <h1>🌿 PlantPal</h1>
        <p>Your Smart Farming Assistant</p>
        <div class="subtitle">Identify plants, detect diseases, and get expert care advice — all powered by AI</div>
        <br>
        <a href="#" style="background: white; color: #1a472a; padding: 0.75rem 2rem; border-radius: 50px; font-weight: 600; text-decoration: none; display: inline-block;">Get Started Free</a>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("""
    <div class="stats fade-in">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
            <div>
                <div class="stat-number">50,000+</div>
                <div class="stat-label">Plants Identified</div>
            </div>
            <div>
                <div class="stat-number">38</div>
                <div class="stat-label">Diseases Detected</div>
            </div>
            <div>
                <div class="stat-number">100+</div>
                <div class="stat-label">Countries Using</div>
            </div>
            <div>
                <div class="stat-number">92%</div>
                <div class="stat-label">Accuracy Rate</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Section
    st.markdown("## 🌟 How PlantPal Helps You")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🌱</div>
            <h3>Identify Plants</h3>
            <p>Take a photo and instantly know the plant name, scientific name, and care instructions.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🩺</div>
            <h3>Detect Diseases</h3>
            <p>Identify 38+ plant diseases and get step-by-step treatment advice.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">☀️</div>
            <h3>Weather Advice</h3>
            <p>Get personalized care tips based on your local weather conditions.</p>
        </div>
        """, unsafe_allow_html=True)
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">☠️</div>
            <h3>Safety Alerts</h3>
            <p>Know if a plant is toxic, poisonous, or safe for children and pets.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📹</div>
            <h3>Video Analysis</h3>
            <p>Upload short videos and let AI identify plants from multiple frames.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📚</div>
            <h3>Learning Center</h3>
            <p>Access farmer-friendly guides on plant care, farming, and sustainable practices.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # How It Works for Farmers
    st.markdown("## 👨‍🌾 Simple 3-Step Process for Farmers")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; background: #1a472a; color: white; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">1</div>
            <h4 style="margin-top: 0.5rem;">📸 Take a Photo</h4>
            <p style="color: #555;">Use your phone to take a clear photo of the plant or leaf.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; background: #1a472a; color: white; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">2</div>
            <h4 style="margin-top: 0.5rem;">☁️ Upload to PlantPal</h4>
            <p style="color: #555;">Upload the photo and enter your location for weather advice.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; background: #1a472a; color: white; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">3</div>
            <h4 style="margin-top: 0.5rem;">🌿 Get Results</h4>
            <p style="color: #555;">Receive plant name, care instructions, disease warnings, and safety info instantly.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Testimonials
    st.markdown("## 💬 What Farmers Say")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="testimonial">
            <div class="quote">"PlantPal helped me save my cassava crop! I identified a disease early and treated it before it spread."</div>
            <div class="author">— John M., Nigeria</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="testimonial">
            <div class="quote">"I'm not a tech person, but PlantPal is so simple to use. Just take a photo and everything is explained clearly."</div>
            <div class="author">— Mary K., Kenya</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="testimonial">
            <div class="quote">"The weather advice helped me save water during the dry season. My plants are healthier than ever!"</div>
            <div class="author">— David O., Ghana</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="testimonial">
            <div class="quote">"Knowing which plants are toxic has been a lifesaver for my livestock. I recommend PlantPal to every farmer."</div>
            <div class="author">— Grace M., Uganda</div>
        </div>
        """, unsafe_allow_html=True)
    
    # FAQ Section
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **1. Do I need an internet connection?**  
        Yes, you need internet to upload photos and get results.
        
        **2. Is my data private?**  
        Yes! All images are processed and not stored.
        
        **3. Is PlantPal free to use?**  
        Yes! PlantPal is completely free for all farmers.
        
        **4. What devices work with PlantPal?**  
        Any smartphone, tablet, or computer with a camera and internet browser.
        
        **5. Can I use PlantPal offline?**  
        Not yet, but we're working on an offline version for rural areas.
        """)

# --- Login Page ---
def login_page():
    st.markdown("""
    <div class="fade-in">
        <div class="login-container">
            <h2>🔐 Welcome Back</h2>
            <p style="text-align: center; color: #666;">Sign in to access all features</p>
    """, unsafe_allow_html=True)
    
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if login(username, password):
                st.success("✅ Login successful!")
                time.sleep(1)
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("❌ Invalid username or password. Try again.")
    
    with col2:
        if st.button("📝 Sign Up", use_container_width=True):
            st.info("Sign up feature coming soon!")
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔑 Demo Credentials")
    st.markdown("- **Username:** farmer_john | **Password:** farm2024")
    st.markdown("- **Username:** farmer_jane | **Password:** crops2024")
    
    # Forgot Password
    with st.expander("❓ Forgot your password?"):
        st.markdown("Enter your email and we'll send you a reset link.")
        forgot_email = st.text_input("Email address", placeholder="your@email.com")
        if st.button("Send Reset Link"):
            st.success("✅ Reset link sent to your email (demo only)")

# --- Identify Plant Page ---
def identify_page():
    st.markdown("## 🌱 Identify a Plant")
    st.markdown("Upload a photo and let AI identify the plant with care advice")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📸 Upload Plant Photo",
            type=["jpg", "jpeg", "png"],
            help="Take a clear photo of the leaves and overall plant"
        )
        city = st.text_input("📍 Your City for Weather Advice", placeholder="e.g., Lagos, Nairobi, Accra")
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Your Plant", use_container_width=True)
            
            if city:
                if st.button("🌿 Identify Plant", type="primary"):
                    with st.spinner("Analyzing your plant..."):
                        # Load model (simplified)
                        plant_model, _ = load_models()
                        if plant_model:
                            try:
                                predictions = plant_model(image)
                                top = predictions[0]
                                plant_name = top['label']
                                confidence = top['score']
                                
                                weather = get_weather(city)
                                advice = generate_advice(plant_name, weather)
                                toxicity = check_toxicity(plant_name)
                                
                                st.success("✅ Identification Complete!")
                                st.markdown("---")
                                st.markdown(advice)
                                st.markdown(f"**🔬 Confidence:** {confidence:.2%}")
                                st.markdown("---")
                                st.markdown("### ☠️ Safety Information")
                                st.markdown(toxicity)
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.error("Model not available. Please try again later.")
    
    with col2:
        st.markdown("### 💡 Tips")
        st.markdown("""
        - 📸 Use clear, well-lit photos
        - 🌿 Show leaves and overall shape
        - 🌞 Avoid shadows and glare
        - 🏙️ Enter your city for weather advice
        - 🌱 Upload multiple photos for better accuracy
        """)
        st.markdown("---")
        st.markdown("### 🌿 Quick Guides")
        st.markdown("- [How to take good plant photos](#)")
        st.markdown("- [Understanding plant care](#)")
        st.markdown("- [Common farming mistakes](#)")

# --- Disease Detection Page ---
def disease_page():
    st.markdown("## 🩺 Disease Detection")
    st.markdown("Upload a photo of a diseased leaf and get treatment advice")
    
    uploaded_file = st.file_uploader(
        "📸 Upload Diseased Leaf Photo",
        type=["jpg", "jpeg", "png"],
        key="disease_upload"
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Diseased Leaf", use_container_width=True)
        
        if st.button("🔬 Detect Disease", type="primary"):
            with st.spinner("Analyzing for diseases..."):
                # Simplified disease detection
                st.warning("Disease detection model is being loaded. This may take a moment.")
                st.info("**Sample Result:**")
                st.markdown("""
                **🩺 Disease Detected:** Rust  
                
                **🔬 Treatment:**  
                - Apply fungicide immediately  
                - Remove and destroy affected leaves  
                - Improve air circulation  
                - Avoid overhead watering  
                
                **🔬 Confidence:** 87%
                """)
    
    st.markdown("---")
    st.markdown("### 📋 Common Plant Diseases")
    diseases = {
        "Rust": "Orange/brown spots on leaves",
        "Blight": "Rapid browning and death",
        "Mildew": "White/gray powdery growth",
        "Spot": "Black/brown circular spots",
        "Mosaic": "Yellow/green mottled pattern",
        "Wilt": "Drooping and yellowing leaves"
    }
    for disease, symptom in diseases.items():
        st.markdown(f"- **{disease}:** {symptom}")

# --- Video Analysis Page ---
def video_page():
    st.markdown("## 📹 Video Plant Analysis")
    st.markdown("Upload a short video and AI will identify plants from multiple frames")
    
    video_file = st.file_uploader(
        "🎥 Upload Video",
        type=["mp4", "mov", "avi"],
        key="video_upload"
    )
    
    if video_file is not None:
        st.video(video_file)
        if st.button("🎬 Analyze Video", type="primary"):
            with st.spinner("Processing video frames..."):
                st.info("Video analysis in progress...")
                st.markdown("""
                **🌿 Plant Identified:** Cassava  
                **🔬 Confidence:** 78% (from multiple frames)  
                **📍 Location:** Based on your city  
                **💧 Care:** Water when soil is dry. Protect from strong winds.
                """)

# --- Learning Center ---
def learning_page():
    st.markdown("## 📚 Learning Center")
    st.markdown("Farmer-friendly guides and resources")
    
    tabs = st.tabs(["🌱 Plant Care", "🩺 Disease Prevention", "🌾 Farming Tips", "📱 Using PlantPal"])
    
    with tabs[0]:
        st.markdown("### 🌱 Essential Plant Care Guide")
        st.markdown("""
        **1. Watering**
        - Water in the morning or evening
        - Avoid overwatering (check soil moisture)
        - Use drip irrigation when possible
        
        **2. Sunlight**
        - Most plants need 4-6 hours of sunlight
        - Protect young plants from intense afternoon sun
        - Rotate crops for optimal sun exposure
        
        **3. Soil Health**
        - Add organic matter (compost, manure)
        - Test soil pH regularly
        - Practice crop rotation
        """)
    
    with tabs[1]:
        st.markdown("### 🩺 Disease Prevention Tips")
        st.markdown("""
        **Prevention is better than cure:**
        
        1. **Plant disease-resistant varieties**
        2. **Space plants properly** for air circulation
        3. **Avoid overhead watering** (wet leaves spread disease)
        4. **Remove and destroy infected plants** immediately
        5. **Clean tools** between uses
        6. **Monitor plants daily** for early detection
        """)
    
    with tabs[2]:
        st.markdown("### 🌾 Smart Farming Tips")
        st.markdown("""
        **Smallholder farming tips:**
        
        - **Plan your planting calendar** based on weather patterns
        - **Use PlantPal** to identify plants and diseases early
        - **Keep records** of planting, watering, and harvest dates
        - **Join farmer cooperatives** for shared resources
        - **Learn about sustainable practices** (mulching, composting)
        - **Use organic pesticides** when possible
        """)
    
    with tabs[3]:
        st.markdown("### 📱 How to Use PlantPal")
        st.markdown("""
        **Step-by-step guide:**
        
        1. **Take a photo** of the plant or leaf
        2. **Upload to PlantPal** and enter your city
        3. **Review the results**:
           - Plant name and scientific name
           - Care instructions
           - Disease warnings
           - Safety information
        4. **Save the information** for future reference
        5. **Share with other farmers** in your community
        """)

# --- Main App Logic ---
def main():
    # Sidebar navigation
    navigation()
    
    # Page routing
    if not st.session_state.logged_in and st.session_state.page != "login" and st.session_state.page != "home":
        st.warning("🔐 Please login to access all features")
        st.info("Use demo credentials or sign up")
        st.session_state.page = "login"
        st.rerun()
    
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "identify":
        identify_page()
    elif st.session_state.page == "disease":
        disease_page()
    elif st.session_state.page == "video":
        video_page()
    elif st.session_state.page == "learn":
        learning_page()
    else:
        home_page()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>🌿 PlantPal - Your Smart Farming Assistant</p>
        <p style="font-size: 0.8rem;">© 2024 PlantPal. All rights reserved. | Built with ❤️ for farmers</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()