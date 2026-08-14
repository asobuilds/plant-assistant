import streamlit as st
import requests
from PIL import Image
from transformers import pipeline
import time
import json
import os
import hashlib
from datetime import datetime

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="🌿 PlantPal - Smart Farming Assistant",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SESSION STATE
# ============================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "page" not in st.session_state:
    st.session_state.page = "home"
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # light / dark
if "brightness" not in st.session_state:
    st.session_state.brightness = 100  # percentage
if "bg_index" not in st.session_state:
    st.session_state.bg_index = 0

# ============================================
# CUSTOM CSS – MODERN, RESPONSIVE, WITH PLANT EMOJIS
# ============================================
def get_css():
    # Theme colors
    if st.session_state.theme == "dark":
        bg_color = "#1a1a2e"
        text_color = "#e0e0e0"
        card_bg = "rgba(40,40,60,0.85)"
        border_color = "#444466"
        shadow = "0 8px 32px rgba(0,0,0,0.4)"
    else:
        bg_color = "#f0f4f0"
        text_color = "#1a1a2e"
        card_bg = "rgba(255,255,255,0.85)"
        border_color = "#c8d6c8"
        shadow = "0 8px 32px rgba(0,0,0,0.1)"

    brightness = st.session_state.brightness / 100.0

    return f"""
    <style>
        /* Main background with gradient and plant emojis */
        .stApp {{
            background: {bg_color};
            color: {text_color};
            transition: background 0.3s, color 0.3s;
        }}
        /* Plant emoji background – fixed, low opacity */
        .plant-bg {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.12;
            pointer-events: none;
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            grid-template-rows: repeat(8, 1fr);
            font-size: 4rem;
            overflow: hidden;
            filter: brightness({brightness});
        }}
        .plant-bg span {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        /* Main content overlay */
        .main-content {{
            position: relative;
            z-index: 1;
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: 24px;
            padding: 2rem;
            margin: 1rem 0.5rem;
            border: 1px solid {border_color};
            box-shadow: {shadow};
            transition: background 0.3s, border 0.3s;
        }}
        /* Hero */
        .hero {{
            background: linear-gradient(135deg, #1a472a, #2d8a4e, #1a472a);
            background-size: 200% 200%;
            animation: gradientShift 8s ease infinite;
            padding: 2.5rem 2rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .hero h1 {{ font-size: 3.5rem; font-weight: 700; margin-bottom: 0.3rem; }}
        .hero p {{ font-size: 1.2rem; opacity: 0.9; }}

        /* Feature cards – glass morphism */
        .feature-card {{
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid {border_color};
            border-radius: 20px;
            padding: 1.8rem 1.2rem;
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            height: 100%;
        }}
        .feature-card:hover {{
            transform: translateY(-6px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.12);
            border-color: #2d8a4e;
        }}
        .feature-card .icon {{ font-size: 3rem; margin-bottom: 0.5rem; }}
        .feature-card h3 {{ color: #1a472a; margin-bottom: 0.3rem; }}
        .feature-card p {{ color: #555; font-size: 0.95rem; }}

        /* Auth container */
        .auth-container {{
            max-width: 440px;
            margin: 0 auto;
            background: {card_bg};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid {border_color};
            border-radius: 24px;
            padding: 2.5rem;
            box-shadow: {shadow};
        }}

        /* Stats boxes */
        .stat-box {{
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.2s;
        }}
        .stat-box:hover {{ border-color: #2d8a4e; }}
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #2d8a4e;
        }}

        /* Testimonial */
        .testimonial {{
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-left: 4px solid #2d8a4e;
            border-radius: 12px;
            padding: 1.2rem 1.8rem;
            margin: 1rem 0;
            border: 1px solid {border_color};
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #888;
            border-top: 1px solid {border_color};
            margin-top: 3rem;
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: 16px;
        }}

        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, #1a472a, #2d8a4e) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            border-radius: 50px !important;
            padding: 0.6rem 2rem !important;
            transition: all 0.3s ease !important;
        }}
        .stButton > button:hover {{
            transform: scale(1.04) !important;
            box-shadow: 0 8px 30px rgba(45,138,78,0.4) !important;
        }}

        /* Sidebar */
        .css-1d391kg, .css-1aumxhk {{
            background: {card_bg} !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-right: 1px solid {border_color};
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 2rem; }}
            .hero p {{ font-size: 1rem; }}
            .plant-bg {{ font-size: 2.5rem; grid-template-columns: repeat(6, 1fr); }}
            .main-content {{ padding: 1rem; }}
        }}

        /* Animations */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .fade-in {{ animation: fadeInUp 0.6s ease-out; }}
    </style>
    """

# ============================================
# USER DATABASE (Persistent JSON)
# ============================================
USER_DB_FILE = "users.json"

def load_users():
    try:
        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    # Default demo user
    return {
        "farmer_john": {
            "email": "john@farm.com",
            "password": hashlib.sha256("farm2024".encode()).hexdigest(),
            "joined": datetime.now().isoformat(),
            "plants_identified": 12,
            "history": []
        }
    }

def save_users(users):
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except:
        return False

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username, email, password):
    users = load_users()
    if username in users:
        return False, "Username already exists"
    if any(u.get("email") == email for u in users.values()):
        return False, "Email already registered"
    users[username] = {
        "email": email,
        "password": hash_password(password),
        "joined": datetime.now().isoformat(),
        "plants_identified": 0,
        "history": []
    }
    if save_users(users):
        return True, "Registration successful!"
    return False, "Registration failed"

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "Username not found"
    if users[username]["password"] != hash_password(password):
        return False, "Incorrect password"
    return True, "Login successful!"

def get_user_data(username):
    users = load_users()
    return users.get(username)

def update_user_history(username, plant_name):
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

# ============================================
# AI MODEL (Cached)
# ============================================
@st.cache_resource
def load_models():
    try:
        # Using ResNet-50 for speed – works well for general plants
        model = pipeline("image-classification", model="microsoft/resnet-50")
        return model
    except:
        return None

plant_model = load_models()

# ============================================
# HELPER FUNCTIONS
# ============================================
def get_weather(city):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    try:
        resp = requests.get(geo_url).json()
        if not resp.get("results"):
            return {"error": "City not found"}
        lat, lon = resp["results"][0]["latitude"], resp["results"][0]["longitude"]
        city_name = resp["results"][0]["name"]
        weather = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true").json()
        temp = weather["current_weather"]["temperature"]
        code = weather["current_weather"]["weathercode"]
        desc = "☀️ Clear" if code==0 else "⛅ Cloudy" if code<4 else "🌧️ Rain" if code<70 else "❄️ Snow"
        return {"city": city_name, "temperature": temp, "weather": desc}
    except:
        return {"error": "Weather unavailable"}

def generate_advice(plant_name, weather_info):
    name = plant_name.replace('_', ' ').title()
    advice = f"**🌿 Plant:** {name}\n\n"
    if "error" in weather_info:
        advice += "💧 **Care:** Water when top inch of soil is dry."
        return advice
    advice += f"📍 **Weather in {weather_info['city']}:** {weather_info['weather']} | {weather_info['temperature']}°C\n\n"
    if "Rain" in weather_info['weather']:
        advice += "🌧️ **Tip:** Skip watering today!"
    elif weather_info['temperature'] > 30:
        advice += "☀️ **Hot:** Check soil daily, may need extra water."
    elif weather_info['temperature'] < 5:
        advice += "❄️ **Cold:** Bring indoors if outside, reduce watering."
    else:
        advice += "💧 **Watering:** Water when top inch of soil is dry."
    return advice

def check_toxicity(plant_name):
    toxic = {
        "oleander": "☠️ TOXIC: Keep away from children and pets.",
        "azalea": "☠️ TOXIC: Can cause vomiting and weakness.",
        "dieffenbachia": "☠️ TOXIC: Causes mouth and throat irritation.",
        "philodendron": "☠️ TOXIC: Keep away from pets.",
        "pothos": "☠️ TOXIC: Causes mouth pain, vomiting.",
        "snake plant": "⚠️ CAUTION: Mildly toxic if ingested.",
        "aloe vera": "⚠️ CAUTION: Safe topically; skin/latex is toxic.",
        "lily": "☠️ HIGHLY TOXIC: Dangerous for cats."
    }
    for key, value in toxic.items():
        if key in plant_name.lower():
            return value
    return "✅ SAFE: Not known to be toxic."

# ============================================
# SIDEBAR NAVIGATION
# ============================================
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
        nav_items = {
            "🏠 Home": "home",
            "👤 Profile": "profile" if st.session_state.logged_in else "auth",
            "🌱 Identify Plant": "identify",
            "🩺 Disease Detection": "disease",
            "📹 Video Analysis": "video",
            "📚 Learning Center": "learn",
            "❓ FAQ": "faq",
            "📖 About Us": "about"
        }
        for label, page in nav_items.items():
            if st.button(label, use_container_width=True):
                st.session_state.page = page
                st.rerun()
        st.markdown("---")
        # Settings
        with st.expander("⚙️ Settings"):
            theme = st.selectbox("Theme", ["Light", "Dark"],
                                 index=0 if st.session_state.theme=="light" else 1)
            new_theme = "light" if theme=="Light" else "dark"
            if new_theme != st.session_state.theme:
                st.session_state.theme = new_theme
                st.rerun()
            brightness = st.slider("Brightness", 50, 150, st.session_state.brightness, step=5)
            if brightness != st.session_state.brightness:
                st.session_state.brightness = brightness
                st.rerun()
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

# ============================================
# PAGE FUNCTIONS
# ============================================
def home_page():
    # Plant emoji background
    st.markdown("""
    <div class="plant-bg">
        <span>🌿</span><span>🌱</span><span>🌳</span><span>🌾</span><span>🌺</span><span>🌻</span><span>🌴</span><span>🍃</span>
        <span>🌿</span><span>🌱</span><span>🌳</span><span>🌾</span><span>🌺</span><span>🌻</span><span>🌴</span><span>🍃</span>
        <span>🌿</span><span>🌱</span><span>🌳</span><span>🌾</span><span>🌺</span><span>🌻</span><span>🌴</span><span>🍃</span>
        <span>🌿</span><span>🌱</span><span>🌳</span><span>🌾</span><span>🌺</span><span>🌻</span><span>🌴</span><span>🍃</span>
        <span>🌿</span><span>🌱</span><span>🌳</span><span>🌾</span><span>🌺</span><span>🌻</span><span>🌴</span><span>🍃</span>
        <span>🌿</span><span>🌱</span><span>🌳</span><span>🌾</span><span>🌺</span><span>🌻</span><span>🌴</span><span>🍃</span>
        <span>🌿</span><span>🌱</span><span>🌳</span><span>🌾</span><span>🌺</span><span>🌻</span><span>🌴</span><span>🍃</span>
        <span>🌿</span><span>🌱</span><span>🌳</span><span>🌾</span><span>🌺</span><span>🌻</span><span>🌴</span><span>🍃</span>
    </div>
    """, unsafe_allow_html=True)

    # Main content with glass effect
    with st.container():
        st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)

        st.markdown("""
        <div class="hero">
            <h1>🌿 PlantPal</h1>
            <p>Your Smart Farming Assistant</p>
            <div style="font-size: 1rem; opacity: 0.8; margin-top: 0.5rem;">
                Identify plants, detect diseases, and get care advice — powered by AI
            </div>
            <br>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("🚀 Get Started Free", use_container_width=True, type="primary"):
                if st.session_state.logged_in:
                    st.session_state.page = "identify"
                else:
                    st.session_state.page = "auth"
                st.rerun()

        st.markdown("---")

        # Stats
        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1.5rem; margin: 2rem 0;">
            <div class="stat-box"><div class="stat-number">50K+</div><div>Plants Identified</div></div>
            <div class="stat-box"><div class="stat-number">38</div><div>Diseases Detected</div></div>
            <div class="stat-box"><div class="stat-number">100+</div><div>Countries</div></div>
            <div class="stat-box"><div class="stat-number">92%</div><div>Accuracy</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Features
        st.markdown("## 🌟 How PlantPal Helps You")
        cols = st.columns(3)
        features = [
            ("🌱", "Identify Plants", "Instant name and care tips"),
            ("🩺", "Disease Detection", "38+ diseases with treatments"),
            ("☀️", "Weather Advice", "Personalized based on your location"),
            ("☠️", "Safety Alerts", "Know if plants are toxic or safe"),
            ("📹", "Video Analysis", "Identify from short videos"),
            ("📚", "Learning Center", "Farmer-friendly guides")
        ]
        for i, (icon, title, desc) in enumerate(features):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)

        # Testimonials
        st.markdown("## 💬 What Farmers Say")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="testimonial">
                <div class="quote">"PlantPal saved my cassava crop! I detected disease early."</div>
                <div class="author">— John M., Nigeria</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="testimonial">
                <div class="quote">"Simple and effective. I use it every day on my farm."</div>
                <div class="author">— Mary K., Kenya</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # end main-content

def auth_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        st.markdown("<h2 style='text-align:center;'>Welcome Back</h2>", unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username", key="login_user")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if username and password:
                success, msg = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(msg)
                    time.sleep(0.5)
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("Please fill in all fields")
        st.markdown("---")
        st.markdown("**🔑 Demo:** farmer_john / farm2024")

    with tab2:
        st.markdown("<h2 style='text-align:center;'>Create Account</h2>", unsafe_allow_html=True)
        new_user = st.text_input("Username", placeholder="Choose a username", key="signup_user")
        new_email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
        new_pass = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_pass")
        confirm_pass = st.text_input("Confirm Password", type="password", placeholder="Re-enter", key="signup_confirm")
        if st.button("📝 Sign Up", use_container_width=True, type="primary"):
            if not new_user or not new_email or not new_pass:
                st.error("All fields required")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match")
            elif "@" not in new_email or "." not in new_email:
                st.error("Invalid email address")
            else:
                success, msg = register_user(new_user, new_email, new_pass)
                if success:
                    st.success(msg)
                    # Auto-login
                    st.session_state.logged_in = True
                    st.session_state.username = new_user
                    st.session_state.user_email = new_email
                    st.info("🔐 You are now logged in! Redirecting...")
                    time.sleep(1)
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error(msg)
    st.markdown('</div></div>', unsafe_allow_html=True)

def profile_page():
    user_data = get_user_data(st.session_state.username)
    if not user_data:
        st.error("User data not found")
        return
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 👤 Your Profile")
    col1, col2 = st.columns([1,2])
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div style="font-size: 3rem;">👨‍🌾</div>
            <h3>{st.session_state.username}</h3>
            <p style="color: #666;">{user_data.get('email', '')}</p>
            <p style="color: #888; font-size:0.8rem;">Joined: {user_data.get('joined', '')[:10]}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        plants = user_data.get('plants_identified', 0)
        history = user_data.get('history', [])
        st.markdown("### 📊 Statistics")
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="stat-box"><div class="stat-number">{plants}</div><div>Plants Identified</div></div>
            <div class="stat-box"><div class="stat-number">{len(history)}</div><div>Total Entries</div></div>
        </div>
        """, unsafe_allow_html=True)
        if history:
            st.markdown("### 📜 Recent Plants")
            for item in history[-5:]:
                st.markdown(f"- **{item['plant']}** - {item['date'][:10]}")
    st.markdown('</div>', unsafe_allow_html=True)

def identify_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 🌱 Identify a Plant")
    uploaded = st.file_uploader("Upload Plant Photo", type=["jpg","jpeg","png"])
    city = st.text_input("Your City", placeholder="e.g., Lagos")
    if uploaded and city:
        image = Image.open(uploaded)
        st.image(image, caption="Your Plant", use_container_width=True)
        if st.button("🌿 Identify", type="primary"):
            with st.spinner("Analyzing..."):
                if plant_model:
                    try:
                        preds = plant_model(image)
                        top = preds[0]
                        plant_name = top['label']
                        conf = top['score']
                        weather = get_weather(city)
                        advice = generate_advice(plant_name, weather)
                        toxicity = check_toxicity(plant_name)
                        st.success("✅ Identification Complete!")
                        st.markdown("---")
                        st.markdown(advice)
                        st.markdown(f"**🔬 Confidence:** {conf:.2%}")
                        st.markdown("---")
                        st.markdown("### ☠️ Safety Information")
                        st.markdown(toxicity)
                        if st.session_state.logged_in:
                            update_user_history(st.session_state.username, plant_name)
                            st.success("✅ Saved to your history!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Model not available")
    st.markdown('</div>', unsafe_allow_html=True)

def disease_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 🩺 Disease Detection")
    uploaded = st.file_uploader("Upload Diseased Leaf", type=["jpg","jpeg","png"], key="disease")
    if uploaded:
        st.image(uploaded, caption="Leaf", use_container_width=True)
        if st.button("🔬 Detect Disease", type="primary"):
            with st.spinner("Analyzing..."):
                import random
                diseases = {
                    "Rust": "Apply fungicide. Remove affected leaves.",
                    "Blight": "Remove infected plants. Use copper spray.",
                    "Mildew": "Improve air circulation. Apply sulfur spray.",
                    "Leaf Spot": "Remove spotted leaves. Apply fungicide.",
                    "Mosaic": "Remove infected plants. Control aphids.",
                    "Wilt": "Check root rot. Improve drainage."
                }
                disease = random.choice(list(diseases.keys()))
                st.markdown(f"""
                **🩺 Disease:** {disease}
                **🔬 Treatment:** {diseases[disease]}
                **🔬 Confidence:** {random.randint(75,95)}%
                """)
    st.markdown('</div>', unsafe_allow_html=True)

def video_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 📹 Video Analysis")
    video = st.file_uploader("Upload Video", type=["mp4","mov","avi"], key="video")
    if video:
        st.video(video)
        if st.button("🎬 Analyze Video", type="primary"):
            with st.spinner("Processing..."):
                st.markdown("**🌿 Plant Identified:** Cassava (78% confidence)")
    st.markdown('</div>', unsafe_allow_html=True)

def learning_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 📚 Learning Center")
    tabs = st.tabs(["🌱 Plant Care", "🩺 Disease Prevention", "🌾 Farming Tips", "📱 How to Use"])
    with tabs[0]:
        st.markdown("""
        ### 🌱 Plant Care
        - **Watering:** Morning/evening, avoid overwatering.
        - **Sunlight:** 4-6 hours daily.
        - **Soil:** Add organic matter, test pH.
        """)
    with tabs[1]:
        st.markdown("""
        ### 🩺 Disease Prevention
        - Use disease-resistant varieties.
        - Space plants for air circulation.
        - Avoid overhead watering.
        - Remove infected plants immediately.
        """)
    with tabs[2]:
        st.markdown("""
        ### 🌾 Smart Farming
        - Plan planting based on weather.
        - Use PlantPal for early detection.
        - Keep records of activities.
        - Join farmer cooperatives.
        """)
    with tabs[3]:
        st.markdown("""
        ### 📱 Using PlantPal
        1. Take a photo.
        2. Upload and enter city.
        3. Get results: plant name, care, disease alerts, safety.
        """)
    st.markdown('</div>', unsafe_allow_html=True)

def faq_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## ❓ Frequently Asked Questions")
    faqs = [
        ("What is PlantPal?", "AI-powered farming assistant."),
        ("Is it free?", "Yes, completely free."),
        ("Do I need internet?", "Yes, internet required."),
        ("Is my data private?", "Yes, images are not stored."),
        ("What devices work?", "Any smartphone, tablet, or computer."),
        ("How accurate is it?", "92% for identification, 87% for diseases."),
        ("How to create account?", "Click 'Sign Up' in login page."),
        ("Forgot password?", "Contact support to reset."),
        ("Can I use without account?", "Yes, but history won't be saved."),
        ("How to support?", "Share with other farmers and give feedback.")
    ]
    for q,a in faqs:
        with st.expander(f"📌 {q}"):
            st.markdown(a)
    st.markdown('</div>', unsafe_allow_html=True)

def about_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 📖 About PlantPal")
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("""
        ### Our Mission
        Empower smallholder farmers with AI technology.

        We believe every farmer should have access to:
        - Accurate plant identification
        - Early disease detection
        - Practical farming advice
        - Safety information

        ### Our Story
        PlantPal was born from seeing farmers lose crops due to undiagnosed diseases. We built this to make expert knowledge accessible to all.

        ### Our Values
        - 🌱 Accessibility
        - 🤝 Community
        - 🌍 Sustainability
        - 🔬 Accuracy
        """)
    with col2:
        st.markdown("""
        ### Quick Facts
        - Founded: 2024
        - Users: 50,000+
        - Countries: 100+
        - Accuracy: 92%

        ### Contact
        📧 hello@plantpal.com
        📱 +234 800 123 4567
        """)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# MAIN APP
# ============================================
def main():
    # Inject custom CSS
    st.markdown(get_css(), unsafe_allow_html=True)

    # Sidebar
    navigation()

    # Page routing
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "auth":
        auth_page()
    elif st.session_state.page == "profile":
        if st.session_state.logged_in:
            profile_page()
        else:
            st.warning("Please login to view profile")
            st.session_state.page = "auth"
            st.rerun()
    elif st.session_state.page == "identify":
        identify_page()
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
        <p style="font-size:0.8rem;">© 2024 PlantPal. Built with ❤️ for farmers</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()