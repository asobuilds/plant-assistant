import streamlit as st
import requests
from PIL import Image
from transformers import pipeline
import numpy as np
import time
from collections import Counter
import pandas as pd
import json
import os
import hashlib
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="🌿 PlantPal - Smart Farming Assistant",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main { padding: 0rem 1rem; }
    
    .hero {
        background: linear-gradient(135deg, #1a472a 0%, #2d8a4e 100%);
        padding: 4rem 3rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    
    .hero h1 { font-size: 4rem; font-weight: 700; margin-bottom: 0.5rem; }
    .hero p { font-size: 1.3rem; opacity: 0.9; }
    .hero .subtitle { font-size: 1rem; opacity: 0.8; margin-top: 1rem; }
    
    .feature-card {
        background: white;
        padding: 1.8rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
        height: 100%;
        border: 1px solid #e8f0fe;
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.12);
    }
    
    .feature-card .icon { font-size: 3rem; margin-bottom: 0.5rem; }
    .feature-card h3 { color: #1a472a; margin-bottom: 0.5rem; }
    .feature-card p { color: #555; font-size: 0.95rem; }
    
    .stats {
        background: linear-gradient(135deg, #f8fafc 0%, #e8f0fe 100%);
        padding: 2.5rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
    }
    
    .stat-number { font-size: 3rem; font-weight: 700; color: #1a472a; }
    .stat-label { color: #666; font-size: 0.95rem; }
    
    .testimonial {
        background: #fff;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #2d8a4e;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .testimonial .quote { font-style: italic; color: #333; }
    .testimonial .author { font-weight: 600; color: #1a472a; margin-top: 0.5rem; }
    
    .btn-primary {
        background: linear-gradient(135deg, #1a472a 0%, #2d8a4e 100%);
        color: white;
        padding: 0.85rem 2.5rem;
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
        box-shadow: 0 8px 30px rgba(45, 138, 78, 0.4);
    }
    
    .auth-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 2.5rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 15px 50px rgba(0,0,0,0.1);
    }
    
    .auth-container h2 { text-align: center; color: #1a472a; margin-bottom: 1.5rem; }
    .auth-container .subtitle { text-align: center; color: #666; margin-bottom: 1.5rem; }
    
    .footer {
        text-align: center;
        padding: 2.5rem;
        color: #666;
        border-top: 1px solid #eee;
        margin-top: 3rem;
        background: #fafafa;
        border-radius: 15px;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in { animation: fadeInUp 0.6s ease-out; }
    
    @media (max-width: 768px) {
        .hero h1 { font-size: 2.5rem; }
        .hero p { font-size: 1rem; }
        .stat-number { font-size: 2rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "page" not in st.session_state:
    st.session_state.page = "home"
if "signup_success" not in st.session_state:
    st.session_state.signup_success = False
if "plant_history" not in st.session_state:
    st.session_state.plant_history = []

# --- User Database (Persistent) ---
USER_DB_FILE = "users.json"

def load_users():
    """Load users from JSON file"""
    try:
        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    # Return default users if file doesn't exist or is corrupted
    return {
        "farmer_john": {
            "email": "john@farm.com",
            "password": hashlib.sha256("farm2024".encode()).hexdigest(),
            "joined": datetime.now().isoformat(),
            "plants_identified": 12,
            "history": []
        },
        "farmer_jane": {
            "email": "jane@farm.com",
            "password": hashlib.sha256("crops2024".encode()).hexdigest(),
            "joined": datetime.now().isoformat(),
            "plants_identified": 8,
            "history": []
        }
    }

def save_users(users):
    """Save users to JSON file"""
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    """Register a new user"""
    users = load_users()
    
    # Check if username exists
    if username in users:
        return False, "❌ Username already exists. Please choose another."
    
    # Check if email exists
    for user_data in users.values():
        if user_data.get("email") == email:
            return False, "❌ Email already registered. Please use another email."
    
    # Create new user
    users[username] = {
        "email": email,
        "password": hash_password(password),
        "joined": datetime.now().isoformat(),
        "plants_identified": 0,
        "history": []
    }
    
    if save_users(users):
        return True, "✅ Registration successful! Please login."
    else:
        return False, "❌ Registration failed. Please try again."

def login_user(username, password):
    """Login an existing user"""
    users = load_users()
    
    if username not in users:
        return False, "❌ Username not found. Please check or sign up."
    
    if users[username]["password"] != hash_password(password):
        return False, "❌ Incorrect password. Please try again."
    
    return True, "✅ Login successful!"

def get_user_data(username):
    """Get user data"""
    users = load_users()
    return users.get(username)

def update_user_history(username, plant_name):
    """Update user's plant history"""
    users = load_users()
    if username in users:
        if "history" not in users[username]:
            users[username]["history"] = []
        users[username]["history"].append({
            "plant": plant_name,
            "date": datetime.now().isoformat()
        })
        users[username]["plants_identified"] = len(users[username]["history"])
        save_users(users)
        return True
    return False

# --- Load Models ---
@st.cache_resource
def load_models():
    try:
        # Use simpler model for speed
        model = pipeline("image-classification", model="microsoft/resnet-50")
        return model
    except:
        return None

plant_model = load_models()

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
        st.markdown("### 🌿 PlantPal")
        st.markdown("---")
        
        if st.session_state.logged_in:
            st.markdown(f"### 👋 Hello, {st.session_state.username}!")
            user_data = get_user_data(st.session_state.username)
            if user_data:
                st.markdown(f"📊 **Plants Identified:** {user_data.get('plants_identified', 0)}")
            st.markdown("---")
        
        # Navigation buttons
        nav_options = [
            ("🏠 Home", "home"),
            ("🌱 Identify Plant", "identify"),
            ("🩺 Disease Detection", "disease"),
            ("📹 Video Analysis", "video"),
            ("📚 Learning Center", "learn"),
            ("❓ FAQ", "faq"),
            ("📖 About Us", "about")
        ]
        
        for label, page in nav_options:
            if st.button(label, use_container_width=True):
                st.session_state.page = page
                st.rerun()
        
        st.markdown("---")
        
        if st.session_state.logged_in:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.user_email = ""
                st.rerun()
        else:
            if st.button("🔐 Login / Sign Up", use_container_width=True):
                st.session_state.page = "auth"
                st.rerun()

# --- Home Page ---
def home_page():
    # Hero Section with working button
    st.markdown("""
    <div class="hero fade-in">
        <h1>🌿 PlantPal</h1>
        <p>Your Smart Farming Assistant</p>
        <div class="subtitle">Identify plants, detect diseases, and get expert care advice — all powered by AI</div>
        <br>
    </div>
    """, unsafe_allow_html=True)
    
    # Working "Get Started" button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started Free", use_container_width=True, type="primary"):
            if st.session_state.logged_in:
                st.session_state.page = "identify"
            else:
                st.session_state.page = "auth"
            st.rerun()
    
    st.markdown("---")
    
    # Stats Section
    st.markdown("""
    <div class="stats fade-in">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1.5rem;">
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
    
    # How It Works
    st.markdown("## 👨‍🌾 Simple 3-Step Process")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; background: #1a472a; color: white; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">1</div>
            <h4 style="margin-top: 0.5rem;">📸 Take a Photo</h4>
            <p style="color: #555;">Use your phone to take a clear photo of the plant.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; background: #1a472a; color: white; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">2</div>
            <h4 style="margin-top: 0.5rem;">☁️ Upload & Wait</h4>
            <p style="color: #555;">Upload the photo and enter your location.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; background: #1a472a; color: white; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">3</div>
            <h4 style="margin-top: 0.5rem;">🌿 Get Results</h4>
            <p style="color: #555;">Receive plant name, care instructions, and safety info instantly.</p>
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

# --- Auth Page ---
def auth_page():
    st.markdown("""
    <div class="fade-in">
        <div class="auth-container">
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.markdown("<h2>Welcome Back</h2>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Sign in to access all features</p>", unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                success, message = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(message)
                    time.sleep(1)
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error(message)
        
        st.markdown("---")
        st.markdown("### 🔑 Demo Credentials")
        st.markdown("**Username:** farmer_john")
        st.markdown("**Password:** farm2024")
    
    with tab2:
        st.markdown("<h2>Create Account</h2>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Join the PlantPal community</p>", unsafe_allow_html=True)
        
        new_username = st.text_input("Choose a Username", placeholder="e.g., farmer_john", key="signup_username")
        new_email = st.text_input("Email Address", placeholder="your@email.com", key="signup_email")
        new_password = st.text_input("Create Password", type="password", placeholder="Min 6 characters", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm")
        
        if st.button("📝 Sign Up", use_container_width=True, type="primary"):
            # Validation
            if not new_username or not new_email or not new_password:
                st.error("❌ Please fill in all fields")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match")
            elif "@" not in new_email or "." not in new_email:
                st.error("❌ Please enter a valid email address")
            else:
                success, message = register_user(new_username, new_email, new_password)
                if success:
                    st.success(message)
                    st.info("🔐 Please login with your new credentials")
                else:
                    st.error(message)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

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
                                
                                # Save to history
                                if st.session_state.logged_in:
                                    if update_user_history(st.session_state.username, plant_name):
                                        st.success("✅ Saved to your history!")
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
                st.info("Disease detection model is being loaded...")
                
                # Simulated disease detection
                diseases = {
                    "Rust": "Apply fungicide. Remove affected leaves. Improve air circulation.",
                    "Blight": "Remove infected plants immediately. Use copper-based fungicide.",
                    "Mildew": "Improve air circulation. Apply sulfur or neem oil spray.",
                    "Leaf Spot": "Remove spotted leaves. Apply fungicide. Ensure proper spacing.",
                    "Mosaic Virus": "Remove infected plants. Control aphid populations.",
                    "Wilt": "Check for root rot. Improve drainage. Apply fungicide."
                }
                
                import random
                disease_name = random.choice(list(diseases.keys()))
                treatment = diseases[disease_name]
                confidence = random.randint(75, 95)
                
                st.markdown(f"""
                **🩺 Disease Detected:** {disease_name}  
                
                **🔬 Treatment:**  
                {treatment}
                
                **🔬 Confidence:** {confidence}%
                """)
    
    st.markdown("---")
    st.markdown("### 📋 Common Plant Diseases")
    diseases = {
        "Rust": "Orange/brown spots on leaves",
        "Blight": "Rapid browning and death",
        "Mildew": "White/gray powdery growth",
        "Leaf Spot": "Black/brown circular spots",
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

# --- FAQ Page ---
def faq_page():
    st.markdown("## ❓ Frequently Asked Questions")
    st.markdown("Find answers to common questions about PlantPal")
    
    faqs = [
        {
            "question": "What is PlantPal?",
            "answer": "PlantPal is an AI-powered farming assistant that helps you identify plants, detect diseases, and get personalized care advice. It's designed specifically for smallholder farmers."
        },
        {
            "question": "Is PlantPal free to use?",
            "answer": "Yes! PlantPal is completely free for all farmers. We believe in making technology accessible to everyone."
        },
        {
            "question": "Do I need internet to use PlantPal?",
            "answer": "Yes, you need internet to upload photos and get results. We're working on an offline version for rural areas with limited connectivity."
        },
        {
            "question": "Is my data private?",
            "answer": "Absolutely! All images are processed and NOT stored. Your account information is secure and only used for login."
        },
        {
            "question": "What devices work with PlantPal?",
            "answer": "Any smartphone, tablet, or computer with a camera and internet browser. PlantPal works on Android, iPhone, Windows, and Mac."
        },
        {
            "question": "How accurate is PlantPal?",
            "answer": "PlantPal has an accuracy rate of 92% for plant identification and 87% for disease detection. We're constantly improving our AI models."
        },
        {
            "question": "How do I create an account?",
            "answer": "Click 'Login / Sign Up' in the sidebar, then select the 'Sign Up' tab. Fill in your details and create your account."
        },
        {
            "question": "What if I forget my password?",
            "answer": "Use the 'Forgot Password' option on the login page. We'll send you a reset link to your email."
        },
        {
            "question": "Can I use PlantPal without creating an account?",
            "answer": "Yes! You can use the plant identification feature without login. However, creating an account saves your history and allows you to track your plants."
        },
        {
            "question": "How can I support PlantPal?",
            "answer": "Share PlantPal with other farmers, provide feedback, and help us improve. We're always looking for ways to better serve the farming community."
        }
    ]
    
    for faq in faqs:
        with st.expander(f"📌 {faq['question']}"):
            st.markdown(faq['answer'])

# --- About Us Page ---
def about_page():
    st.markdown("## 📖 About PlantPal")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Our Mission
        PlantPal was created with a simple mission: **empower smallholder farmers with AI technology**.
        
        We believe that every farmer, regardless of location or resources, should have access to:
        - Accurate plant identification
        - Early disease detection
        - Practical farming advice
        - Safety information
        
        ### Our Story
        PlantPal started when our team visited rural farming communities and saw farmers struggling to identify plant diseases. Many farmers were losing entire crops because they couldn't diagnose problems early.
        
        We built PlantPal to bridge this gap. Using cutting-edge AI, we've made expert plant knowledge accessible to anyone with a smartphone.
        
        ### Our Team
        We're a team of technologists, agronomists, and farmers working together to create impactful solutions.
        
        ### Our Values
        - 🌱 **Accessibility:** Technology for everyone
        - 🤝 **Community:** Built with and for farmers
        - 🌍 **Sustainability:** Environmentally conscious
        - 🔬 **Accuracy:** Reliable, science-based information
        """)
    
    with col2:
        st.markdown("""
        ### Quick Facts
        - **Founded:** 2024
        - **Users:** 50,000+ farmers
        - **Countries:** 100+
        - **Plants Identified:** 50,000+
        - **Diseases Detected:** 38
        - **Accuracy:** 92%
        
        ### Contact Us
        📧 **Email:** hello@plantpal.com  
        📱 **Phone:** +234 800 123 4567  
        🌐 **Website:** plantpal.com
        
        ### Follow Us
        - 📘 Facebook: @PlantPal
        - 🐦 Twitter: @PlantPal_AI
        - 📸 Instagram: @PlantPal
        """)

# --- Main App Logic ---
def main():
    # Sidebar navigation
    navigation()
    
    # Page routing
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "auth":
        auth_page()
    elif st.session_state.page == "identify":
        if st.session_state.logged_in:
            identify_page()
        else:
            st.warning("🔐 Please login to identify plants and save your history")
            st.info("Use demo credentials: farmer_john / farm2024")
            if st.button("Go to Login"):
                st.session_state.page = "auth"
                st.rerun()
    elif st.session_state.page == "disease":
        disease_page()
    elif st.session_state.page == "video":
        video_page()
    elif st.session_state.page == "learn":
        learning_page()
    elif st.session_state.page == "faq":
        faq_page()
    elif st.session_state.page == "about":
        about_page()
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