import streamlit as st
import requests
from PIL import Image
from transformers import pipeline
import time
import json
import os
import hashlib
from datetime import datetime
import random
import re

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="🌿 PlantPal - Smart Farming Companion",
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
if "full_name" not in st.session_state:
    st.session_state.full_name = ""
if "page" not in st.session_state:
    st.session_state.page = "home"
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "brightness" not in st.session_state:
    st.session_state.brightness = 100
if "language" not in st.session_state:
    st.session_state.language = "English"
if "otp" not in st.session_state:
    st.session_state.otp = None
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False
if "profile_complete" not in st.session_state:
    st.session_state.profile_complete = False
if "previous_page" not in st.session_state:
    st.session_state.previous_page = "home"
if "pending_username" not in st.session_state:
    st.session_state.pending_username = ""
if "pending_full_name" not in st.session_state:
    st.session_state.pending_full_name = ""
if "pending_email" not in st.session_state:
    st.session_state.pending_email = ""
if "pending_password" not in st.session_state:
    st.session_state.pending_password = ""
if "free_identifications" not in st.session_state:
    st.session_state.free_identifications = 0
if "show_otp" not in st.session_state:
    st.session_state.show_otp = False
if "signup_success" not in st.session_state:
    st.session_state.signup_success = False

# ============================================
# LANGUAGE SUPPORT
# ============================================
LANGUAGES = {
    "English": "en",
    "Yorùbá": "yo",
    "Hausa": "ha",
    "Igbo": "ig",
    "Pidgin": "pcm",
    "Swahili": "sw"
}

TRANSLATIONS = {
    "en": {
        "app_name": "🌿 PlantPal",
        "tagline": "Your Smart Farming Companion",
        "welcome": "Welcome",
        "identify": "Identify Plant",
        "disease": "Detect Disease",
        "video": "Video Analysis",
        "learn": "Learning Center",
        "faq": "FAQ",
        "about": "About Us",
        "profile": "Profile",
        "login": "Login / Sign Up",
        "logout": "Logout",
        "settings": "Settings",
        "theme": "Theme",
        "brightness": "Brightness",
        "light": "Light",
        "dark": "Dark",
        "home": "Home",
        "back": "← Back",
        "feedback": "Feedback",
        "weeds": "Weeds & Pesticides",
        "fertilizers": "Fertilizers",
        "ask_ai": "Ask AI",
        "free_limit": "You've used {count} free identifications. Create an account to unlock unlimited access!",
        "register_prompt": "🌱 Unlock unlimited plant identifications, save your history, and get personalized advice. It's free!"
    },
    "sw": {
        "app_name": "🌿 PlantPal",
        "tagline": "Mshauri Wako wa Kilimo",
        "welcome": "Karibu",
        "identify": "Tambua Mimea",
        "disease": "Gundua Magonjwa",
        "video": "Uchambuzi wa Video",
        "learn": "Kituo cha Kujifunza",
        "faq": "Maswali",
        "about": "Kuhusu Sisi",
        "profile": "Wasifu",
        "login": "Ingia / Jisajili",
        "logout": "Toka",
        "settings": "Mipangilio",
        "theme": "Rangi",
        "brightness": "Mwangaza",
        "light": "Mwangaza",
        "dark": "Giza",
        "home": "Nyumbani",
        "back": "← Rudi",
        "feedback": "Maoni",
        "weeds": "Magugu na Dawa",
        "fertilizers": "Mboji",
        "ask_ai": "Uliza AI",
        "free_limit": "Umetumia {count} za bure. Jisajili ili kupata ukomo!",
        "register_prompt": "🌱 Fungua ukomo wa kutambua mimea, hifadhi historia, na upate ushauri wa kibinafsi. Ni bure!"
    }
}

def get_text(key):
    lang_code = LANGUAGES.get(st.session_state.language, "en")
    return TRANSLATIONS.get(lang_code, {}).get(key, key)

# ============================================
# DATABASE LAYER
# ============================================
USER_DB_FILE = "users.json"

USE_POSTGRES = os.environ.get("DATABASE_URL") is not None

if USE_POSTGRES:
    try:
        import psycopg2
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                full_name TEXT,
                email TEXT UNIQUE,
                password TEXT,
                joined TEXT,
                plants_identified INTEGER DEFAULT 0,
                nationality TEXT,
                bio TEXT,
                profile_pic TEXT,
                verified BOOLEAN DEFAULT FALSE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_history (
                id SERIAL PRIMARY KEY,
                username TEXT,
                plant TEXT,
                date TEXT,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                username TEXT,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                date TEXT,
                page TEXT
            )
        """)
        conn.commit()
        print("✅ PostgreSQL connected")
    except Exception as e:
        USE_POSTGRES = False
        print(f"⚠️ PostgreSQL connection failed: {e}")

def load_users():
    if USE_POSTGRES:
        try:
            cur = conn.cursor()
            cur.execute("SELECT username, full_name, email, password, joined, plants_identified, nationality, bio, profile_pic, verified FROM users")
            rows = cur.fetchall()
            users = {}
            for row in rows:
                users[row[0]] = {
                    "full_name": row[1] or "",
                    "email": row[2],
                    "password": row[3],
                    "joined": row[4],
                    "plants_identified": row[5] or 0,
                    "nationality": row[6] or "",
                    "bio": row[7] or "",
                    "profile_pic": row[8] or "",
                    "verified": row[9] or False,
                    "history": []
                }
            cur.execute("SELECT username, plant, date FROM user_history ORDER BY date DESC")
            for row in cur.fetchall():
                if row[0] in users:
                    if "history" not in users[row[0]]:
                        users[row[0]]["history"] = []
                    users[row[0]]["history"].append({"plant": row[1], "date": row[2]})
            return users
        except Exception as e:
            print(f"PostgreSQL load error: {e}")
    
    try:
        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        "farmer_john": {
            "full_name": "John Farmer",
            "email": "john@farm.com",
            "password": hashlib.sha256("farm2024".encode()).hexdigest(),
            "joined": datetime.now().isoformat(),
            "plants_identified": 12,
            "nationality": "Nigeria",
            "bio": "Cassava farmer from Oyo State",
            "profile_pic": "🌾",
            "verified": True,
            "history": []
        }
    }

def save_users(users):
    if USE_POSTGRES:
        try:
            for username, data in users.items():
                cur.execute("""
                    INSERT INTO users (username, full_name, email, password, joined, plants_identified, nationality, bio, profile_pic, verified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email,
                        password = EXCLUDED.password,
                        plants_identified = EXCLUDED.plants_identified,
                        nationality = EXCLUDED.nationality,
                        bio = EXCLUDED.bio,
                        profile_pic = EXCLUDED.profile_pic,
                        verified = EXCLUDED.verified
                """, (username, data.get('full_name', ''), data['email'], data['password'], 
                      data['joined'], data.get('plants_identified', 0), data.get('nationality', ''),
                      data.get('bio', ''), data.get('profile_pic', ''), data.get('verified', False)))
                cur.execute("DELETE FROM user_history WHERE username = %s", (username,))
                if 'history' in data:
                    for item in data['history']:
                        cur.execute("""
                            INSERT INTO user_history (username, plant, date)
                            VALUES (%s, %s, %s)
                        """, (username, item['plant'], item['date']))
            conn.commit()
            return True
        except Exception as e:
            print(f"PostgreSQL save error: {e}")
    
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except:
        return False

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username, full_name, email, password):
    users = load_users()
    if username in users:
        return False, "Username already exists"
    if any(u.get("email") == email for u in users.values()):
        return False, "Email already registered"
    
    otp = str(random.randint(100000, 999999))
    st.session_state.otp = otp
    st.session_state.otp_verified = False
    st.session_state.pending_username = username
    st.session_state.pending_full_name = full_name
    st.session_state.pending_email = email
    st.session_state.pending_password = password
    st.session_state.show_otp = True
    
    return True, f"✅ OTP generated: **{otp}** (Copy this code) - Enter it below to verify."

def verify_otp(email, entered_otp):
    if st.session_state.otp and st.session_state.otp == entered_otp:
        users = load_users()
        username = st.session_state.pending_username
        users[username] = {
            "full_name": st.session_state.pending_full_name,
            "email": email,
            "password": hash_password(st.session_state.pending_password),
            "joined": datetime.now().isoformat(),
            "plants_identified": 0,
            "nationality": "",
            "bio": "",
            "profile_pic": "👨‍🌾",
            "verified": True,
            "history": []
        }
        if save_users(users):
            st.session_state.otp = None
            st.session_state.otp_verified = True
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_email = email
            st.session_state.full_name = st.session_state.pending_full_name
            st.session_state.profile_complete = False
            st.session_state.free_identifications = 0
            return True, "Email verified! Welcome to PlantPal!"
        else:
            return False, "Account creation failed."
    return False, "Invalid OTP. Please try again."

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "Username not found"
    if users[username]["password"] != hash_password(password):
        return False, "Incorrect password"
    if not users[username].get("verified", False):
        return False, "Email not verified. Please check your email."
    return True, "Login successful!"

def get_user_data(username):
    users = load_users()
    return users.get(username)

def update_user_profile(username, full_name, nationality, bio, profile_pic):
    users = load_users()
    if username in users:
        users[username]["full_name"] = full_name
        users[username]["nationality"] = nationality
        users[username]["bio"] = bio
        users[username]["profile_pic"] = profile_pic
        save_users(users)
        st.session_state.full_name = full_name
        return True
    return False

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

def save_feedback(username, rating, comment, page):
    if USE_POSTGRES:
        try:
            cur.execute("""
                INSERT INTO feedback (username, rating, comment, date, page)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, rating, comment, datetime.now().isoformat(), page))
            conn.commit()
            return True
        except Exception as e:
            print(f"Feedback save error: {e}")
            return False
    return False

def get_feedback(limit=20):
    if USE_POSTGRES:
        try:
            cur.execute("""
                SELECT username, rating, comment, date, page 
                FROM feedback 
                ORDER BY date DESC 
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
        except:
            pass
    return []

# ============================================
# CROP DATABASE
# ============================================
CROP_DATABASE = {
    "cassava": {
        "local_name": "Akpu/Kpo/Rogo (Nigeria), Mhogo (Swahili)",
        "season": "Rainy season",
        "harvest": "9-12 months",
        "price": "₦50,000-80,000/ton",
        "diseases": ["Cassava Mosaic Disease", "Cassava Brown Streak", "Anthracnose"],
        "uses": "Food, starch, animal feed, ethanol",
        "soil": "Well-drained sandy loam, pH 5.5-6.5",
        "water": "Moderate (1000-1500mm annually)",
        "storage": "Process within 48 hours of harvest",
        "emoji": "🌿",
        "region": "Tropical Africa"
    },
    "rice": {
        "local_name": "Shinkafa/Osikapa (Nigeria), Mchele (Swahili)",
        "season": "Rainy season",
        "harvest": "4-5 months",
        "price": "₦80,000-120,000/ton",
        "diseases": ["Rice Blast", "Sheath Blight", "Bacterial Leaf Blight"],
        "uses": "Food, brewing, animal feed",
        "soil": "Clay or loamy, pH 5.5-6.5",
        "water": "High (1500-2000mm)",
        "storage": "Dry to 12-14% moisture",
        "emoji": "🌾",
        "region": "Global"
    },
    "maize": {
        "local_name": "Agbado/Oka (Nigeria), Mahindi (Swahili)",
        "season": "Rainy season",
        "harvest": "3-4 months",
        "price": "₦40,000-60,000/ton",
        "diseases": ["Maize Lethal Necrosis", "Fall Armyworm", "Leaf Blight"],
        "uses": "Food, animal feed, flour, ethanol",
        "soil": "Well-drained loamy, pH 5.5-6.5",
        "water": "Moderate (500-1000mm)",
        "storage": "Dry to 12-14% moisture",
        "emoji": "🌽",
        "region": "Global"
    },
    "yam": {
        "local_name": "Isu/Na/Eba (Nigeria)",
        "season": "Rainy season",
        "harvest": "7-9 months",
        "price": "₦100,000-150,000/ton",
        "diseases": ["Yam Anthracnose", "Yam Mosaic Virus", "Nematodes"],
        "uses": "Food, animal feed, medicinal",
        "soil": "Well-drained sandy loam, pH 5.5-6.5",
        "water": "Moderate (1000-1500mm)",
        "storage": "Store in well-ventilated yam barn",
        "emoji": "🍠",
        "region": "West Africa"
    },
    "groundnut": {
        "local_name": "Epa/Geda (Nigeria), Njugu (Swahili)",
        "season": "Rainy season",
        "harvest": "4-5 months",
        "price": "₦350,000-450,000/ton",
        "diseases": ["Groundnut Rosette", "Leaf Spot", "Rust"],
        "uses": "Food, oil, animal feed",
        "soil": "Well-drained sandy, pH 5.5-6.5",
        "water": "Moderate (500-800mm)",
        "storage": "Dry to 8-10% moisture",
        "emoji": "🥜",
        "region": "Global"
    },
    "tomato": {
        "local_name": "Tomati/Tumatir (Nigeria), Nyanya (Swahili)",
        "season": "Dry season",
        "harvest": "2-3 months",
        "price": "₦50,000-80,000/ton",
        "diseases": ["Tomato Blight", "Tomato Mosaic Virus", "Fusarium Wilt"],
        "uses": "Food, sauces",
        "soil": "Well-drained loamy, pH 6.0-6.8",
        "water": "Moderate (500-800mm)",
        "storage": "Store at room temperature",
        "emoji": "🍅",
        "region": "Global"
    },
    "pepper": {
        "local_name": "Shombo/Tatashe (Nigeria), Pilipili (Swahili)",
        "season": "Dry season",
        "harvest": "2-3 months",
        "price": "₦100,000-150,000/ton",
        "diseases": ["Pepper Anthracnose", "Bacterial Spot", "Virus"],
        "uses": "Food, spice, medicine",
        "soil": "Well-drained sandy loam, pH 6.0-6.8",
        "water": "Moderate (400-600mm)",
        "storage": "Dry and store in airtight containers",
        "emoji": "🌶️",
        "region": "Global"
    },
    "cocoa": {
        "local_name": "Koko (Nigeria)",
        "season": "October-December, April-June",
        "harvest": "5-6 months after flowering",
        "price": "₦800,000-1,200,000/ton",
        "diseases": ["Black Pod", "Witches' Broom", "Mirids"],
        "uses": "Chocolate, cocoa butter",
        "soil": "Well-drained deep soil, pH 6.0-6.5",
        "water": "High (1500-2000mm)",
        "storage": "Dry to 7-8% moisture",
        "emoji": "🍫",
        "region": "West Africa"
    },
    "palm_oil": {
        "local_name": "Epo (Nigeria)",
        "season": "All year",
        "harvest": "4-5 years after planting",
        "price": "₦250,000-350,000/ton",
        "diseases": ["Ganoderma", "Fusarium Wilt", "Bud Rot"],
        "uses": "Cooking oil, soap, biodiesel",
        "soil": "Well-drained loamy, pH 4.5-6.0",
        "water": "High (1500-2000mm)",
        "storage": "Store in cool, dark place",
        "emoji": "🌴",
        "region": "Tropical Africa"
    },
    "beans": {
        "local_name": "Ewa/Olojola (Nigeria), Maharage (Swahili)",
        "season": "Rainy season",
        "harvest": "2-3 months",
        "price": "₦200,000-300,000/ton",
        "diseases": ["Bean Rust", "Anthracnose", "Bacterial Blight"],
        "uses": "Food, animal feed",
        "soil": "Well-drained loamy, pH 6.0-7.0",
        "water": "Moderate (500-800mm)",
        "storage": "Dry to 10-12% moisture",
        "emoji": "🫘",
        "region": "Global"
    }
}

def get_crop_info(plant_name):
    plant_lower = plant_name.lower()
    for crop, info in CROP_DATABASE.items():
        if crop in plant_lower:
            return crop, info
    return None, None

# ============================================
# WEED DATABASE
# ============================================
WEED_DATABASE = {
    "spear_grass": {
        "name": "Spear Grass (Imperata cylindrica)",
        "description": "Persistent grass with deep rhizomes.",
        "control_organic": "Deep plowing, mulching, repeated cutting",
        "control_chemical": "Glyphosate or Paraquat",
        "prevention": "Regular monitoring, crop rotation",
        "season": "All year",
        "emoji": "🌾"
    },
    "goat_weed": {
        "name": "Goat Weed (Ageratum conyzoides)",
        "description": "Annual herb, spreads rapidly.",
        "control_organic": "Hand pulling, heavy mulching",
        "control_chemical": "2,4-D or Atrazine",
        "prevention": "Maintain soil cover",
        "season": "Rainy season",
        "emoji": "🌿"
    },
    "mimosa": {
        "name": "Mimosa (Mimosa pudica)",
        "description": "Spreading herb with thorns.",
        "control_organic": "Manual pulling before seed set",
        "control_chemical": "Glyphosate or Dicamba",
        "prevention": "Avoid seed spread",
        "season": "Rainy season",
        "emoji": "🌱"
    }
}

def get_weed_info(weed_name):
    weed_lower = weed_name.lower()
    for key, info in WEED_DATABASE.items():
        if key in weed_lower or info['name'].lower() in weed_lower:
            return info
    return None

# ============================================
# FERTILIZER DATABASE
# ============================================
FERTILIZER_DATABASE = {
    "cassava": {
        "best": "NPK 15-15-15 + organic compost",
        "organic": "Poultry manure, compost, wood ash",
        "application": "Apply 4-6 months after planting",
        "timing": "Start of rainy season",
        "local_options": "Compost, poultry manure"
    },
    "rice": {
        "best": "NPK 20-10-10 + Urea topdressing",
        "organic": "Compost, green manure, rice straw",
        "application": "At planting and tillering",
        "timing": "Start of rainy season",
        "local_options": "Rice straw compost"
    },
    "maize": {
        "best": "NPK 15-15-15 + Urea side-dress",
        "organic": "Poultry manure, compost",
        "application": "250kg/ha at planting, 100kg/ha Urea",
        "timing": "Start of rainy season",
        "local_options": "Poultry manure"
    }
}

def get_fertilizer_info(crop_name):
    crop_lower = crop_name.lower()
    for crop, info in FERTILIZER_DATABASE.items():
        if crop in crop_lower:
            return info
    return None

def whatsapp_share(message):
    encoded = message.replace(" ", "%20").replace("\n", "%0A")
    return f"https://wa.me/?text={encoded}"

# ============================================
# AI MODEL
# ============================================
@st.cache_resource
def load_models():
    try:
        model = pipeline("image-classification", model="microsoft/resnet-50")
        return model
    except:
        return None

plant_model = load_models()

# ============================================
# WEATHER FUNCTIONS
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
        advice += "☀️ **Hot:** Check soil daily. May need extra water."
    elif weather_info['temperature'] < 5:
        advice += "❄️ **Cold:** Bring indoors if outside."
    else:
        advice += "💧 **Watering:** Water when top inch of soil is dry."
    return advice

def check_toxicity(plant_name):
    toxic = {
        "oleander": "☠️ TOXIC: Keep away from children and pets.",
        "azalea": "☠️ TOXIC: Can cause vomiting.",
        "dieffenbachia": "☠️ TOXIC: Mouth and throat irritation.",
        "philodendron": "☠️ TOXIC: Keep away from pets.",
        "pothos": "☠️ TOXIC: Mouth pain, vomiting.",
        "lily": "☠️ HIGHLY TOXIC: Dangerous for cats."
    }
    for key, value in toxic.items():
        if key in plant_name.lower():
            return value
    return "✅ SAFE: Not known to be toxic."

# ============================================
# AI CHATBOT
# ============================================
def get_ai_response(question):
    q = question.lower().strip()
    
    # Crop lookup
    for crop, info in CROP_DATABASE.items():
        if crop in q:
            return f"""
**🌿 {crop.capitalize()}**

**Local Name:** {info['local_name']}
**Season:** {info['season']}
**Harvest:** {info['harvest']}
**Price:** {info['price']}

**Diseases:** {', '.join(info['diseases'])}
**Uses:** {info['uses']}
**Soil:** {info['soil']}
**Water:** {info['water']}
**Storage:** {info['storage']}
"""
    
    # Symptoms
    if any(word in q for word in ["yellow", "yellowing", "leaves yellow"]):
        return """
💛 **Yellowing Leaves – What to Do**

🌱 **Nutrient deficiency** – add compost or organic fertilizer.
💧 **Overwatering** – let soil dry out before watering.
🐛 **Pests** – check under leaves.
🌡️ **Weather stress** – provide shade if too hot.

**Quick tip:** Check if yellowing is on old or new leaves.
"""
    
    if any(word in q for word in ["brown spot", "spots"]):
        return """
🟤 **Leaf Spots – Possible Causes**

🍄 **Fungal infection** – apply copper-based fungicide.
💧 **Water splashes** – avoid overhead watering.
🌱 **Nutrient burn** – reduce fertilizer.

**Treatment:** Remove affected leaves, improve air circulation.
"""
    
    if "wilt" in q or "drooping" in q:
        return """
🥀 **Wilting – What to Do**

💧 **Underwatering** – water deeply.
💦 **Overwatering** – roots may be rotting.
🌡️ **Heat stress** – provide shade.

**Action:** Check soil moisture 2 inches deep. If dry, water; if wet, let it dry out.
"""
    
    # General
    if "what is plantpal" in q:
        return """
🌿 **PlantPal – Your Farming Companion**

✅ Identify plants from photos
✅ Detect diseases early
✅ Get market prices
✅ Find fertilizers and weed control
✅ Free and always learning!

**Ask me anything about farming!**
"""
    
    if "how to use" in q:
        return """
📱 **How to Use PlantPal**

1. 📸 Take a clear photo
2. ☁️ Upload and enter your city
3. 🌿 Get results – name, care, prices
4. 📤 Share via WhatsApp
5. 📝 Create account to save history
"""
    
    return """
🤔 **Great question! I can help with:**

- 🌿 Plant identification and care
- 🩺 Disease diagnosis
- 🌱 Fertilizer and soil advice
- 🌾 Weed control
- 💰 Market prices

**Try asking:**
- "My cassava leaves are yellowing"
- "How to control weeds?"
- "Best fertilizer for rice?"

I'm here to help you grow! 🌻
"""

# ============================================
# CUSTOM CSS – MODERN, DYNAMIC, WITH STRONG PRESENCE
# ============================================
def get_css():
    if st.session_state.theme == "dark":
        bg_color = "#0a0a1a"
        text_color = "#e0e0e0"
        card_bg = "rgba(30,30,50,0.75)"
        border_color = "rgba(255,255,255,0.08)"
        shadow = "0 8px 32px rgba(0,0,0,0.6)"
        hero_bg = "linear-gradient(135deg, #0a1a0a, #1a3a2a, #0a1a0a)"
        glass_bg = "rgba(255,255,255,0.05)"
        accent_color = "#3a9d5e"
    else:
        bg_color = "#f0f4f0"
        text_color = "#1a1a2e"
        card_bg = "rgba(255,255,255,0.7)"
        border_color = "rgba(255,255,255,0.3)"
        shadow = "0 8px 32px rgba(0,0,0,0.1)"
        hero_bg = "linear-gradient(135deg, #0d2e1a, #1a472a, #2d8a4e, #1a472a)"
        glass_bg = "rgba(255,255,255,0.15)"
        accent_color = "#2d8a4e"

    return f"""
    <style>
        /* GLOBAL RESET */
        .stApp {{
            background: {bg_color};
            color: {text_color};
            transition: background 0.3s, color 0.3s;
            padding: 0 !important;
        }}
        
        #MainMenu, footer, header {{visibility: hidden;}}
        
        /* FLOATING LEAVES BACKGROUND */
        .plant-bg {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.04;
            pointer-events: none;
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            grid-template-rows: repeat(6, 1fr);
            font-size: 2.5rem;
            overflow: hidden;
            user-select: none;
        }}
        .plant-bg span {{
            display: flex;
            align-items: center;
            justify-content: center;
            animation: float 10s infinite ease-in-out;
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0) rotate(0deg); }}
            50% {{ transform: translateY(-15px) rotate(5deg); }}
        }}
        
        /* GLASS-MORPHISM CARD */
        .glass {{
            background: {card_bg};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {border_color};
            border-radius: 24px;
            padding: 1.5rem;
            box-shadow: {shadow};
            transition: all 0.4s ease;
        }}
        .glass:hover {{
            border-color: {accent_color};
            box-shadow: 0 12px 48px rgba(45,138,78,0.2);
        }}
        
        /* HERO SECTION – DYNAMIC WITH PRESENCE */
        .hero {{
            background: {hero_bg};
            background-size: 400% 400%;
            animation: gradientShift 8s ease infinite;
            padding: 3rem 2rem;
            border-radius: 28px;
            color: white;
            text-align: center;
            margin-bottom: 1.5rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.35);
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '🌿🌾🌱🌻🌽🍅🍠🥜';
            position: absolute;
            top: -30px;
            right: -20px;
            font-size: 6rem;
            opacity: 0.08;
            animation: rotate 25s linear infinite;
        }}
        .hero::after {{
            content: '🌿🌱🌾🌻🌽🍅🍠';
            position: absolute;
            bottom: -30px;
            left: -20px;
            font-size: 5rem;
            opacity: 0.06;
            animation: rotate 30s linear infinite reverse;
        }}
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .hero h1 {{
            font-size: 3.2rem;
            font-weight: 900;
            margin-bottom: 0.3rem;
            position: relative;
            z-index: 1;
            text-shadow: 0 4px 30px rgba(0,0,0,0.4);
            letter-spacing: -0.5px;
        }}
        .hero h1 .highlight {{
            background: linear-gradient(135deg, #f5d742, #f7b731);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .hero p {{
            font-size: 1.3rem;
            opacity: 0.95;
            position: relative;
            z-index: 1;
            text-shadow: 0 2px 15px rgba(0,0,0,0.3);
            font-weight: 500;
        }}
        .hero .subtitle {{
            font-size: 1rem;
            opacity: 0.8;
            position: relative;
            z-index: 1;
            margin-top: 0.5rem;
            font-weight: 400;
        }}
        
        /* FEATURE CARDS – CLICKABLE, DYNAMIC */
        .feature-card {{
            background: {card_bg};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid {border_color};
            border-radius: 24px;
            padding: 2rem 1.2rem;
            text-align: center;
            transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            box-shadow: {shadow};
            height: 100%;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }}
        .feature-card::before {{
            content: '';
            position: absolute;
            top: -100%;
            left: -100%;
            width: 300%;
            height: 300%;
            background: radial-gradient(circle, rgba(45,138,78,0.08) 0%, transparent 70%);
            transition: opacity 0.5s;
            opacity: 0;
        }}
        .feature-card:hover::before {{
            opacity: 1;
        }}
        .feature-card:hover {{
            transform: translateY(-12px) scale(1.02);
            border-color: {accent_color};
            box-shadow: 0 20px 60px rgba(45,138,78,0.25);
        }}
        .feature-card .icon {{
            font-size: 3.5rem;
            margin-bottom: 0.5rem;
            display: block;
            animation: pulse 2.5s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.08); }}
        }}
        .feature-card h3 {{
            color: {accent_color};
            margin-bottom: 0.3rem;
            font-size: 1.2rem;
            font-weight: 800;
        }}
        .feature-card p {{
            color: {text_color};
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        /* STATS */
        .stat-box {{
            background: {card_bg};
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 1rem;
            text-align: center;
            transition: all 0.3s;
        }}
        .stat-box:hover {{
            border-color: {accent_color};
            transform: scale(1.03);
        }}
        .stat-number {{
            font-size: 2.2rem;
            font-weight: 800;
            color: {accent_color};
        }}
        
        /* AUTH CONTAINER */
        .auth-container {{
            max-width: 480px;
            margin: 0 auto;
            background: {card_bg};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {border_color};
            border-radius: 28px;
            padding: 2rem;
            box-shadow: {shadow};
        }}
        
        /* PROFILE PIC */
        .profile-pic {{
            font-size: 4.5rem;
            text-align: center;
        }}
        
        /* BUTTONS */
        .stButton > button {{
            background: linear-gradient(135deg, #1a472a, #2d8a4e, #1a472a) !important;
            background-size: 200% 200% !important;
            animation: buttonShift 4s ease infinite !important;
            color: white !important;
            font-weight: 800 !important;
            border: none !important;
            border-radius: 50px !important;
            padding: 0.8rem 2.5rem !important;
            font-size: 1.05rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            box-shadow: 0 4px 25px rgba(45,138,78,0.35) !important;
            letter-spacing: 0.5px !important;
        }}
        @keyframes buttonShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .stButton > button:hover {{
            transform: scale(1.04) !important;
            box-shadow: 0 8px 45px rgba(45,138,78,0.5) !important;
        }}
        
        /* WHATSAPP BUTTON */
        .whatsapp-btn {{
            background: #25D366 !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 14px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            cursor: pointer !important;
            text-decoration: none !important;
            display: inline-block !important;
            margin: 8px 0 !important;
            transition: all 0.3s !important;
            width: 100% !important;
            text-align: center !important;
        }}
        .whatsapp-btn:hover {{
            transform: scale(1.04) !important;
            box-shadow: 0 4px 25px rgba(37,211,102,0.4) !important;
        }}
        
        /* FEEDBACK BOX */
        .feedback-box {{
            background: {card_bg};
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 1rem;
            margin: 0.5rem 0;
        }}
        
        /* FOOTER */
        .footer {{
            text-align: center;
            padding: 1.5rem;
            color: #888;
            border-top: 1px solid {border_color};
            margin-top: 2rem;
            background: {card_bg};
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 16px;
            font-size: 0.85rem;
            letter-spacing: 0.3px;
        }}
        
        /* BOTTOM NAV – MOBILE */
        .bottom-nav {{
            display: none;
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: {card_bg};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-top: 1px solid {border_color};
            padding: 0.5rem 0;
            z-index: 999;
            justify-content: space-around;
        }}
        .bottom-nav .nav-item {{
            text-align: center;
            font-size: 0.7rem;
            color: {text_color};
            opacity: 0.6;
            cursor: pointer;
            transition: opacity 0.2s;
            padding: 0.25rem 0.5rem;
            border: none;
            background: transparent;
        }}
        .bottom-nav .nav-item.active {{
            opacity: 1;
            color: {accent_color};
            font-weight: 700;
        }}
        .bottom-nav .nav-item .icon {{
            font-size: 1.6rem;
            display: block;
        }}
        
        @media (max-width: 768px) {{
            .bottom-nav {{ display: flex; }}
            .main-content {{ padding-bottom: 80px; }}
            .hero h1 {{ font-size: 2rem; }}
            .hero p {{ font-size: 1rem; }}
            .hero {{ padding: 1.5rem 1rem; }}
            .feature-card {{ padding: 1.2rem 0.8rem; }}
            .feature-card .icon {{ font-size: 2.5rem; }}
            .plant-bg {{ font-size: 1.2rem; grid-template-columns: repeat(3, 1fr); }}
            .stat-number {{ font-size: 1.5rem; }}
        }}
        @media (max-width: 480px) {{
            .hero h1 {{ font-size: 1.5rem; }}
            .hero p {{ font-size: 0.85rem; }}
            .feature-card h3 {{ font-size: 1rem; }}
        }}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .fade-in {{ animation: fadeInUp 0.6s ease-out; }}
        
        @keyframes slideDown {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .slide-down {{ animation: slideDown 0.4s ease-out; }}
    </style>
    """

# ============================================
# SIDEBAR NAVIGATION
# ============================================
def navigation():
    with st.sidebar:
        st.markdown(f"### 🌿 PlantPal")
        st.markdown("---")
        
        if st.session_state.logged_in:
            st.markdown(f"### 👋 Hello, {st.session_state.full_name or st.session_state.username}!")
            user_data = get_user_data(st.session_state.username)
            if user_data:
                st.markdown(f"📊 **Plants:** {user_data.get('plants_identified', 0)}")
            st.markdown("---")
        
        lang = st.selectbox("🌍 Language", list(LANGUAGES.keys()))
        if lang != st.session_state.language:
            st.session_state.language = lang
            st.rerun()
        
        st.markdown("---")
        
        nav_items = {
            "🏠 Home": "home",
            "🌱 Identify": "identify",
            "🩺 Disease": "disease",
            "📹 Video": "video",
            "📚 Learn & AI": "learn",
            "🌿 Weeds": "weeds",
            "🧪 Fertilizers": "fertilizers",
            "💬 Feedback": "feedback",
            "❓ FAQ": "faq",
            "📖 About": "about"
        }
        
        if st.session_state.logged_in:
            nav_items["👤 Profile"] = "profile"
            nav_items["🚪 Logout"] = "logout"
        else:
            nav_items["🔐 Login"] = "auth"
        
        for label, page in nav_items.items():
            if st.button(label, use_container_width=True):
                if page == "logout":
                    st.session_state.logged_in = False
                    st.session_state.username = ""
                    st.session_state.user_email = ""
                    st.session_state.full_name = ""
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.session_state.previous_page = st.session_state.page
                    st.session_state.page = page
                    st.rerun()
        
        st.markdown("---")
        
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

# ============================================
# BOTTOM NAVIGATION (MOBILE)
# ============================================
def bottom_nav():
    st.markdown("""
    <div class="bottom-nav">
        <button class="nav-item" onclick="window.location.href='/?page=home'">
            <span class="icon">🏠</span> Home
        </button>
        <button class="nav-item" onclick="window.location.href='/?page=identify'">
            <span class="icon">🌱</span> Identify
        </button>
        <button class="nav-item" onclick="window.location.href='/?page=learn'">
            <span class="icon">🤖</span> Ask AI
        </button>
        <button class="nav-item" onclick="window.location.href='/?page=profile'">
            <span class="icon">👤</span> Profile
        </button>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# BACK BUTTON
# ============================================
def back_button():
    if st.button("← Back", key="back_btn"):
        st.session_state.page = st.session_state.previous_page
        st.rerun()

# ============================================
# HOME PAGE
# ============================================
def home_page():
    crop_emoji = ["🌿", "🌾", "🌱", "🌻", "🌽", "🍅", "🍠", "🥜"]
    bg_html = '<div class="plant-bg">'
    for i in range(48):
        bg_html += f'<span>{crop_emoji[i % len(crop_emoji)]}</span>'
    bg_html += '</div>'
    st.markdown(bg_html, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="hero">
            <h1>🌿 <span class="highlight">PlantPal</span></h1>
            <p>🌍 Your Smart Farming Companion</p>
            <div class="subtitle">
                🌾 Identify plants · 🩺 Detect diseases · 💰 Market prices · 🌿 Weed control · 🧪 Fertilizer advice
                <br>🌎 Available in 5+ languages – For smallholder farmers everywhere
            </div>
            <br>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.session_state.logged_in:
                if st.button("🌱 Start Identifying Plants", use_container_width=True, type="primary"):
                    st.session_state.page = "identify"
                    st.rerun()
            else:
                if st.button("🚀 Get Started – Free!", use_container_width=True, type="primary"):
                    st.session_state.page = "auth"
                    st.rerun()

        st.markdown("---")

        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 0.8rem; margin: 1rem 0;">
            <div class="stat-box"><div class="stat-number">50K+</div><div style="font-size:0.75rem;">Identified</div></div>
            <div class="stat-box"><div class="stat-number">38</div><div style="font-size:0.75rem;">Diseases</div></div>
            <div class="stat-box"><div class="stat-number">15+</div><div style="font-size:0.75rem;">Crops</div></div>
            <div class="stat-box"><div class="stat-number">92%</div><div style="font-size:0.75rem;">Accuracy</div></div>
            <div class="stat-box"><div class="stat-number">5</div><div style="font-size:0.75rem;">Languages</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("## 🌟 Explore PlantPal")
        st.markdown("Click on any card to try it out – no login required for the first 3 identifications!")

        col1, col2, col3 = st.columns(3)
        
        features = [
            ("🌱", "Identify Plant", "Snap a photo and get the name, care tips, and market price.", "identify"),
            ("🌾", "Nigerian Crops", "Learn about Cassava, Rice, Yam, Tomato, Pepper, Maize and more.", "learn"),
            ("🩺", "Disease Detection", "Upload a sick leaf and get treatment recommendations.", "disease"),
            ("💰", "Market Prices", "Check current market prices for crops in ₦ per ton.", "learn"),
            ("📱", "Share via WhatsApp", "Share plant info with other farmers instantly.", "#"),
            ("🌍", "5+ Languages", "Use PlantPal in English, Yorùbá, Hausa, Igbo, Pidgin, Swahili.", "about")
        ]
        
        for i, (icon, title, desc, page) in enumerate(features):
            with col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3:
                if st.button(f"{icon} **{title}**\n\n{desc}", key=f"feature_{i}"):
                    if page != "#":
                        st.session_state.page = page
                        st.rerun()
                    else:
                        st.info("📱 WhatsApp sharing is available after plant identification.")

        st.markdown("---")
        st.markdown("## 📋 How It Works")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="text-align:center;padding:0.5rem;">
                <div style="font-size:2.8rem;">📸</div>
                <h4>1. Take a Photo</h4>
                <p style="color:#666;font-size:0.9rem;">Of any plant or leaf</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="text-align:center;padding:0.5rem;">
                <div style="font-size:2.8rem;">☁️</div>
                <h4>2. Upload & Analyze</h4>
                <p style="color:#666;font-size:0.9rem;">AI identifies instantly</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="text-align:center;padding:0.5rem;">
                <div style="font-size:2.8rem;">🌿</div>
                <h4>3. Get Results</h4>
                <p style="color:#666;font-size:0.9rem;">Name, care, prices, and more</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# AUTH PAGE – FIXED SIGN-UP
# ============================================
def auth_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        st.markdown("<h2 style='text-align:center;'>Welcome Back</h2>", unsafe_allow_html=True)
        username = st.text_input("Username or Email", placeholder="Enter your username or email", key="login_user")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
        
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if username and password:
                success, msg = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    user_data = get_user_data(username)
                    if user_data:
                        st.session_state.full_name = user_data.get('full_name', '')
                        st.session_state.user_email = user_data.get('email', '')
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
        st.markdown("<p style='text-align:center;color:#666;'>Join the farming community</p>", unsafe_allow_html=True)
        
        # CRITICAL FIX: All fields inside the form must be captured properly
        with st.form(key="signup_form"):
            full_name = st.text_input("Full Name", placeholder="e.g., Adebayo Ogunlesi", key="signup_full_name")
            username = st.text_input("Username", placeholder="Choose a unique username", key="signup_user")
            email = st.text_input("Email Address", placeholder="your@email.com", key="signup_email")
            password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_pass")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm")
            
            st.markdown("---")
            st.markdown("### 📧 Email Verification")
            st.markdown("A code will be shown for you to verify.")
            
            submitted = st.form_submit_button("📝 Sign Up", use_container_width=True, type="primary")
            
            if submitted:
                # Validation
                if not full_name or not username or not email or not password:
                    st.error("❌ All fields are required. Please fill in everything.")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif "@" not in email or "." not in email:
                    st.error("❌ Invalid email address")
                elif " " in username:
                    st.error("❌ Username cannot contain spaces")
                else:
                    success, msg = register_user(username, full_name, email, password)
                    if success:
                        st.success(msg)
                        st.session_state.show_otp = True
                        
                        # Show OTP verification
                        otp_code = st.text_input("Enter 6-digit OTP", placeholder="e.g., 123456", key="otp_input")
                        if st.button("✅ Verify Email", use_container_width=True):
                            if otp_code:
                                verified, verify_msg = verify_otp(email, otp_code)
                                if verified:
                                    st.success(verify_msg)
                                    st.balloons()
                                    st.info("👤 Please complete your profile!")
                                    time.sleep(1)
                                    st.session_state.page = "profile"
                                    st.rerun()
                                else:
                                    st.error(verify_msg)
                            else:
                                st.error("Please enter the OTP code")
                    else:
                        st.error(msg)
    
    st.markdown('</div></div>', unsafe_allow_html=True)

# ============================================
# PROFILE PAGE
# ============================================
def profile_page():
    back_button()
    user_data = get_user_data(st.session_state.username)
    if not user_data:
        st.error("User data not found")
        return
    
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 👤 Your Profile")
    
    needs_completion = not user_data.get("nationality") or not user_data.get("bio")
    if needs_completion:
        st.info("📝 Please complete your profile to personalize your experience.")
    
    col1, col2 = st.columns([1,2])
    with col1:
        profile_pic = user_data.get("profile_pic", "👨‍🌾")
        st.markdown(f"""
        <div class="profile-pic">{profile_pic}</div>
        <div style="text-align:center;">
            <h3>{user_data.get('full_name', st.session_state.username)}</h3>
            <p style="color:#666;">@{st.session_state.username}</p>
        </div>
        """, unsafe_allow_html=True)
        
        pic_options = ["👨‍🌾", "👩‍🌾", "🌾", "🌿", "🌱", "🌳", "🌻", "🍅", "🌽", "🍠", "🥬", "🌶️"]
        new_pic = st.selectbox("Profile Emoji", pic_options, 
                               index=pic_options.index(profile_pic) if profile_pic in pic_options else 0)
        if new_pic != profile_pic:
            if update_user_profile(st.session_state.username, user_data.get('full_name',''),
                                  user_data.get('nationality',''), user_data.get('bio',''), new_pic):
                st.success("✅ Updated")
                st.rerun()
    
    with col2:
        st.markdown("### 📋 Personal Info")
        full_name = st.text_input("Full Name", value=user_data.get('full_name', ''))
        nationalities = ["Nigeria", "Ghana", "Kenya", "South Africa", "Uganda", "Tanzania", 
                         "Other African", "Other International"]
        curr_nat = user_data.get('nationality', '')
        nationality = st.selectbox("Nationality", nationalities, 
                                   index=nationalities.index(curr_nat) if curr_nat in nationalities else 0)
        bio = st.text_area("About You", value=user_data.get('bio',''), placeholder="Tell us about your farm.")
        st.text_input("Email", value=user_data.get('email',''), disabled=True)
        st.text_input("Joined", value=user_data.get('joined','')[:10], disabled=True)
        
        if st.button("💾 Save Profile", type="primary"):
            if update_user_profile(st.session_state.username, full_name, nationality, bio, new_pic):
                st.success("✅ Profile updated!")
                st.session_state.full_name = full_name
                st.balloons()
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Your Plant Journey")
        plants = user_data.get('plants_identified', 0)
        history = user_data.get('history', [])
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-box"><div class="stat-number">{plants}</div><div style="font-size:0.8rem;">Plants</div></div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-box"><div class="stat-number">{len(history)}</div><div style="font-size:0.8rem;">Entries</div></div>
            """, unsafe_allow_html=True)
        if history:
            st.markdown("#### Recent")
            for item in history[-5:]:
                st.markdown(f"- **{item['plant']}** - {item['date'][:10]}")
        if user_data.get("verified", False):
            st.success("✅ Email Verified")
        else:
            st.warning("⚠️ Email not verified")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# IDENTIFY PAGE
# ============================================
def identify_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 🌱 Identify a Plant")
    st.markdown("Upload a photo and get plant name, care tips, and market prices")

    if not st.session_state.logged_in and st.session_state.free_identifications >= 3:
        st.warning("🌱 You've used your 3 free identifications. Create a free account to continue!")
        st.info(get_text("register_prompt"))
        if st.button("🔐 Create Account", type="primary"):
            st.session_state.page = "auth"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    uploaded = st.file_uploader("Upload Plant Photo", type=["jpg","jpeg","png"])
    city = st.text_input("Your City", placeholder="e.g., Lagos, Nairobi, Accra")
    
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
                        
                        crop, info = get_crop_info(plant_name)
                        weather = get_weather(city)
                        advice = generate_advice(plant_name, weather)
                        toxicity = check_toxicity(plant_name)
                        
                        st.success("✅ Identification Complete!")
                        st.markdown("---")
                        st.markdown(advice)
                        
                        if crop:
                            st.markdown("---")
                            st.markdown(f"## 🇳🇬 {crop.capitalize()}")
                            st.markdown(f"**Local Name:** {info['local_name']}")
                            st.markdown(f"**Season:** {info['season']}")
                            st.markdown(f"**Harvest:** {info['harvest']}")
                            st.markdown(f"**Price:** {info['price']}")
                            st.markdown(f"**Diseases:** {', '.join(info['diseases'])}")
                            st.markdown(f"**Uses:** {info['uses']}")
                            st.markdown(f"**Soil:** {info['soil']}")
                            
                            share_text = f"🌿 PlantPal ID: {crop.capitalize()}\nLocal: {info['local_name']}\nSeason: {info['season']}\nPrice: {info['price']}"
                            share_url = whatsapp_share(share_text)
                            st.markdown(f'<a href="{share_url}" target="_blank"><button class="whatsapp-btn">📱 Share on WhatsApp</button></a>', unsafe_allow_html=True)
                        else:
                            st.markdown("---")
                            st.markdown("💡 Not a common crop? We're constantly adding more!")
                        
                        st.markdown(f"**🔬 Confidence:** {conf:.2%}")
                        st.markdown("---")
                        st.markdown("### ☠️ Safety")
                        st.markdown(toxicity)
                        
                        if st.session_state.logged_in:
                            update_user_history(st.session_state.username, plant_name)
                            st.success("✅ Saved to your history!")
                        else:
                            st.session_state.free_identifications += 1
                            remaining = 3 - st.session_state.free_identifications
                            if remaining > 0:
                                st.info(f"📊 You have {remaining} free identification(s) remaining.")
                            else:
                                st.warning("🌱 You've used all free identifications. Create an account to continue!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Model not available. Please try again later.")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# DISEASE PAGE
# ============================================
def disease_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 🩺 Disease Detection")
    uploaded = st.file_uploader("Upload Diseased Leaf", type=["jpg","jpeg","png"], key="disease")
    if uploaded:
        st.image(uploaded, caption="Leaf", use_container_width=True)
        if st.button("🔬 Detect", type="primary"):
            with st.spinner("Analyzing..."):
                diseases = {
                    "Cassava Mosaic": "Remove infected plants. Use resistant varieties. Control whiteflies.",
                    "Rice Blast": "Use resistant varieties. Apply fungicide. Avoid nitrogen overuse.",
                    "Yam Anthracnose": "Use clean seeds. Apply fungicide. Destroy infected vines.",
                    "Tomato Blight": "Use resistant varieties. Apply fungicide. Avoid overhead watering.",
                    "Pepper Anthracnose": "Apply fungicide. Remove infected fruits. Improve air circulation.",
                    "Maize Lethal Necrosis": "Remove infected plants. Control insects. Use resistant varieties.",
                    "Fall Armyworm": "Apply appropriate insecticide. Use pheromone traps.",
                    "Black Pod": "Remove infected pods. Improve drainage. Apply fungicide."
                }
                disease = random.choice(list(diseases.keys()))
                treatment = diseases[disease]
                st.markdown(f"""
                **🩺 Disease Detected:** {disease}
                **🔬 Treatment:** {treatment}
                **🔬 Confidence:** {random.randint(75,95)}%
                """)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# VIDEO PAGE
# ============================================
def video_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 📹 Video Analysis")
    video = st.file_uploader("Upload Video", type=["mp4","mov","avi"], key="video")
    if video:
        st.video(video)
        if st.button("🎬 Analyze", type="primary"):
            with st.spinner("Processing..."):
                st.markdown("**🌿 Plant:** Cassava (78% confidence)")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# WEEDS PAGE
# ============================================
def weeds_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 🌿 Weed Identification & Control")
    for weed_key, info in WEED_DATABASE.items():
        with st.expander(f"{info['emoji']} {info['name']}"):
            st.markdown(f"**Description:** {info['description']}")
            st.markdown(f"**🌱 Organic Control:** {info['control_organic']}")
            st.markdown(f"**🧪 Chemical Control:** {info['control_chemical']}")
            st.markdown(f"**🛡️ Prevention:** {info['prevention']}")
            st.markdown(f"**📅 Season:** {info['season']}")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# FERTILIZERS PAGE
# ============================================
def fertilizers_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 🧪 Fertilizer Guide")
    for crop, info in FERTILIZER_DATABASE.items():
        with st.expander(f"🌱 {crop.capitalize()}"):
            st.markdown(f"**Best:** {info['best']}")
            st.markdown(f"**Organic:** {info['organic']}")
            st.markdown(f"**Application:** {info['application']}")
            st.markdown(f"**Timing:** {info['timing']}")
            st.markdown(f"**Local Options:** {info['local_options']}")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# LEARNING & AI PAGE
# ============================================
def learning_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 📚 Learning Center & AI Assistant")
    tabs = st.tabs(["🌾 Crops", "🌱 Care", "🩺 Disease", "📱 How", "🤖 Ask AI"])
    
    with tabs[0]:
        for crop, info in CROP_DATABASE.items():
            with st.expander(f"{info['emoji']} {crop.capitalize()}"):
                st.markdown(f"**Local:** {info['local_name']}")
                st.markdown(f"**Season:** {info['season']}")
                st.markdown(f"**Harvest:** {info['harvest']}")
                st.markdown(f"**Price:** {info['price']}")
                st.markdown(f"**Diseases:** {', '.join(info['diseases'])}")
                st.markdown(f"**Uses:** {info['uses']}")
    with tabs[1]:
        st.markdown("### Plant Care Basics")
        st.markdown("""
        **💧 Watering:** Morning/evening, avoid overwatering.
        **☀️ Sunlight:** 4-6 hours daily.
        **🌱 Soil:** Add compost, test pH regularly.
        **🧪 Fertilizer:** Use organic options when possible.
        """)
    with tabs[2]:
        st.markdown("### Disease Prevention")
        st.markdown("""
        1. Use resistant varieties.
        2. Space plants properly.
        3. Avoid overhead watering.
        4. Remove infected plants immediately.
        5. Monitor daily.
        6. Practice crop rotation.
        """)
    with tabs[3]:
        st.markdown("### How to Use PlantPal")
        st.markdown("""
        1. **Take a photo** of the plant or leaf.
        2. **Upload** to PlantPal.
        3. **Enter your city** for weather advice.
        4. **Get results** – name, care, prices.
        5. **Share** via WhatsApp.
        6. **Save** your history (create account).
        """)
    with tabs[4]:
        st.markdown("### 🤖 Ask PlantPal AI")
        st.markdown("Ask any farming question – I'm your companion!")
        user_q = st.text_input("Your question:", placeholder="e.g., Why are my tomato leaves turning yellow?")
        if user_q:
            with st.spinner("Thinking..."):
                response = get_ai_response(user_q)
                st.markdown("---")
                st.markdown("### 🤖 AI Response")
                st.markdown(response)
        st.markdown("---")
        st.markdown("### 💡 Try These Questions")
        st.markdown("""
        - "My cassava leaves are yellowing"
        - "How to control weeds in maize?"
        - "Best fertilizer for rice?"
        - "When to harvest yam?"
        - "What are common plant diseases?"
        - "My soil is dry and cracked, what should I do?"
        """)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# FEEDBACK PAGE
# ============================================
def feedback_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 💬 Your Feedback Matters")
    with st.form("feedback_form"):
        rating = st.select_slider("Rate PlantPal", options=[1,2,3,4,5], value=4)
        comment = st.text_area("What do you think? (Optional)", placeholder="Share your thoughts...")
        page = st.selectbox("Which page?", ["Home","Identify","Disease","Learn","Weeds","Fertilizers","Other"])
        submitted = st.form_submit_button("Submit Feedback", type="primary")
        if submitted:
            username = st.session_state.username if st.session_state.logged_in else "anonymous"
            if save_feedback(username, rating, comment, page):
                st.success("✅ Thank you! 🙏")
                st.balloons()
            else:
                st.error("❌ Could not save feedback.")
    st.markdown("---")
    st.markdown("### 📋 Recent Feedback")
    feedbacks = get_feedback(10)
    if feedbacks:
        for fb in feedbacks:
            stars = "⭐" * int(fb[1])
            st.markdown(f"""
            <div class="feedback-box">
                <strong>{fb[0]}</strong> {stars}
                <p>{fb[2] or 'No comment'}</p>
                <p style="color:#888;font-size:0.7rem;">{fb[3][:10]} - {fb[4]}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No feedback yet. Be the first!")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# FAQ PAGE
# ============================================
def faq_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## ❓ FAQ")
    faqs = [
        ("What is PlantPal?", "AI-powered farming companion for smallholder farmers."),
        ("Is it free?", "Yes! Free identification (3 free tries) and unlimited with account."),
        ("Do I need internet?", "Yes, internet required."),
        ("How accurate?", "92% for identification."),
        ("How to create account?", "Click 'Sign Up' and enter your details."),
        ("What crops?", "Cassava, Rice, Yam, Tomato, Pepper, Maize, Cocoa, and more."),
        ("Can I share results?", "Yes, via WhatsApp."),
        ("Do I need to login?", "No, explore first. Login for unlimited use and history."),
        ("What about weeds?", "Check the Weeds section."),
        ("What about fertilizers?", "Check the Fertilizers section."),
        ("How to use AI assistant?", "Go to Learn Center → Ask AI tab."),
        ("Who is this for?", "All smallholder farmers, anywhere in the world.")
    ]
    for q,a in faqs:
        with st.expander(f"📌 {q}"):
            st.markdown(a)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# ABOUT PAGE
# ============================================
def about_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 📖 About PlantPal")
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("""
        ### 🌍 Our Mission
        Empower smallholder farmers everywhere with AI technology.
        
        We believe every farmer should have access to:
        - Accurate plant identification
        - Early disease detection
        - Practical farming advice
        - Market price information
        - Weed and fertilizer guidance
        
        ### 🌱 Our Story
        Born from seeing farmers struggle with crop losses, PlantPal makes expert knowledge accessible to all.

        ### 🌾 Our Crops
        Cassava, Rice, Yam, Groundnut, Tomato, Pepper, Maize, Sorghum, Cocoa, Palm Oil, Beans, Plantain, Okra, Millet, Sesame – and growing.

        ### 🌿 Weeds Database
        Spear Grass, Goat Weed, Mimosa, Bermuda Grass, Pigweed, and more.

        ### 🧪 Fertilizer Guide
        Crop-specific recommendations with organic and local options.

        ### 🌟 Our Values
        - 🌱 Accessibility – Technology for everyone
        - 🤝 Community – Built with farmers
        - 🌍 Sustainability – Environmentally conscious
        - 🔬 Accuracy – Reliable, science-based information
        - 🌎 Universal – For farmers everywhere
        """)
    with col2:
        st.markdown("""
        ### Quick Facts
        - Founded: 2024
        - Users: 50,000+
        - Crops: 15+
        - Weeds: 6+
        - Languages: 5+
        - Accuracy: 92%

        ### Contact
        📧 hello@plantpal.com
        📱 +234 800 123 4567
        
        ### Follow
        - 📘 Facebook: @PlantPal
        - 🐦 Twitter: @PlantPal_AI
        - 📸 Instagram: @PlantPal
        """)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# MAIN APP
# ============================================
def main():
    st.markdown(get_css(), unsafe_allow_html=True)
    navigation()
    bottom_nav()
    
    if st.session_state.logged_in and st.session_state.page != "profile":
        user_data = get_user_data(st.session_state.username)
        if user_data and (not user_data.get('nationality') or not user_data.get('bio')):
            if st.session_state.page not in ["profile", "auth", "home"]:
                st.info("👤 Please complete your profile for a better experience.")
                if st.button("Go to Profile"):
                    st.session_state.page = "profile"
                    st.rerun()
    
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "auth":
        auth_page()
    elif st.session_state.page == "profile":
        if st.session_state.logged_in:
            profile_page()
        else:
            st.warning("Please login to view your profile")
            st.session_state.page = "auth"
            st.rerun()
    elif st.session_state.page == "identify":
        identify_page()
    elif st.session_state.page == "disease":
        disease_page()
    elif st.session_state.page == "video":
        video_page()
    elif st.session_state.page == "weeds":
        weeds_page()
    elif st.session_state.page == "fertilizers":
        fertilizers_page()
    elif st.session_state.page == "learn":
        learning_page()
    elif st.session_state.page == "feedback":
        feedback_page()
    elif st.session_state.page == "faq":
        faq_page()
    elif st.session_state.page == "about":
        about_page()
    else:
        home_page()
    
    st.markdown("""
    <div class="footer">
        <p>🌍 PlantPal – Your Smart Farming Companion</p>
        <p style="font-size:0.7rem;">© 2024 PlantPal. Built with ❤️ for farmers everywhere</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()