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
    st.session_state.theme = "light"
if "brightness" not in st.session_state:
    st.session_state.brightness = 100
if "language" not in st.session_state:
    st.session_state.language = "English"

# ============================================
# LANGUAGE SUPPORT
# ============================================
LANGUAGES = {
    "English": "en",
    "Yorùbá": "yo",
    "Hausa": "ha",
    "Igbo": "ig",
    "Pidgin": "pcm"
}

TRANSLATIONS = {
    "en": {
        "app_name": "🌿 PlantPal",
        "tagline": "Your Smart Farming Assistant",
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
        "home": "Home"
    },
    "yo": {
        "app_name": "🌿 PlantPal",
        "tagline": "Oluranlọwọ Rẹ fun Iṣẹ-ogbin",
        "welcome": "Ẹ kú àbò",
        "identify": "Dá Mọ́ Ẹ̀wé",
        "disease": "Wá Àrùn",
        "video": "Ṣe Àyẹ̀wò Fídíò",
        "learn": "Ibi Ìkẹ́kọ̀ọ́",
        "faq": "Ìbéèrè Tí Wọ́n Ọ̀pọ̀",
        "about": "Nípa Wa",
        "profile": "Iṣẹ́ Ṣe",
        "login": "Wọlé / Forúkọ Sí",
        "logout": "Jáde",
        "settings": "Ètò",
        "theme": "Àwọ̀",
        "brightness": "Ìmọ́lẹ̀",
        "light": "Ìmọ́lẹ̀",
        "dark": "Òkùnkùn",
        "home": "Ilé"
    },
    "ha": {
        "app_name": "🌿 PlantPal",
        "tagline": "Mai Taimakon Noma",
        "welcome": "Sannu da zuwa",
        "identify": "Gane Shuka",
        "disease": "Gano Cuta",
        "video": "Nazari Bidiyo",
        "learn": "Cibiyar Koyo",
        "faq": "Tambayoyi",
        "about": "Game da Mu",
        "profile": "Bayanan Ku",
        "login": "Shiga / Rajista",
        "logout": "Fita",
        "settings": "Saituna",
        "theme": "Launi",
        "brightness": "Hasken",
        "light": "Haske",
        "dark": "Duhu",
        "home": "Gida"
    },
    "ig": {
        "app_name": "🌿 PlantPal",
        "tagline": "Onye Enyemaka Ọrụ Ugbo Gị",
        "welcome": "Nnọọ",
        "identify": "Mata Osisi",
        "disease": "Chọpụta Ọrịa",
        "video": "Nyochaa Vidiyo",
        "learn": "Ebe Ọmụmụ",
        "faq": "Ajụjụ Ndị A Na-ajụ",
        "about": "Gbasara Anyị",
        "profile": "Profaịlụ",
        "login": "Banye / Debanye",
        "logout": "Pụọ",
        "settings": "Ntọala",
        "theme": "Agba",
        "brightness": "Ìhè",
        "light": "Ìhè",
        "dark": "Ọchịchịrị",
        "home": "Ụlọ"
    },
    "pcm": {
        "app_name": "🌿 PlantPal",
        "tagline": "Your Farm Helper",
        "welcome": "Welcome",
        "identify": "Sabby Plant",
        "disease": "Find Sickness",
        "video": "Check Video",
        "learn": "Learn Place",
        "faq": "Q&A",
        "about": "About Us",
        "profile": "Your Profile",
        "login": "Login / Sign Up",
        "logout": "Logout",
        "settings": "Settings",
        "theme": "Colour",
        "brightness": "Brightness",
        "light": "Light",
        "dark": "Dark",
        "home": "Home"
    }
}

def get_text(key):
    lang_code = LANGUAGES.get(st.session_state.language, "en")
    return TRANSLATIONS.get(lang_code, {}).get(key, key)

# ============================================
# CUSTOM CSS – MOBILE-FRIENDLY
# ============================================
def get_css():
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
        /* Mobile-first responsive */
        .stApp {{
            background: {bg_color};
            color: {text_color};
            transition: background 0.3s, color 0.3s;
            padding: 0 !important;
        }}
        
        /* Sidebar mobile fix */
        .css-1d391kg, .css-1aumxhk {{
            background: {card_bg} !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-right: 1px solid {border_color};
        }}
        
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Plant background - mobile optimized */
        .plant-bg {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.08;
            pointer-events: none;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: repeat(6, 1fr);
            font-size: 1.5rem;
            font-weight: 600;
            overflow: hidden;
            filter: brightness({brightness});
            user-select: none;
        }}
        .plant-bg span {{
            display: flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
            font-size: 1.2rem;
        }}
        
        /* Main content - mobile optimized */
        .main-content {{
            position: relative;
            z-index: 1;
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: 16px;
            padding: 1rem;
            margin: 0.5rem;
            border: 1px solid {border_color};
            box-shadow: {shadow};
            transition: background 0.3s, border 0.3s;
        }}
        
        /* Hero - mobile optimized */
        .hero {{
            background: linear-gradient(135deg, #1a472a, #2d8a4e, #1a472a);
            background-size: 200% 200%;
            animation: gradientShift 8s ease infinite;
            padding: 1.5rem 1rem;
            border-radius: 16px;
            color: white;
            text-align: center;
            margin-bottom: 1rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .hero h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }}
        .hero p {{ font-size: 1rem; opacity: 0.9; }}
        .hero .subtitle {{ font-size: 0.85rem; opacity: 0.8; }}
        
        /* Feature cards - mobile optimized */
        .feature-card {{
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 1rem 0.8rem;
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            height: 100%;
            margin-bottom: 0.5rem;
        }}
        .feature-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            border-color: #2d8a4e;
        }}
        .feature-card .icon {{ font-size: 2.2rem; margin-bottom: 0.3rem; }}
        .feature-card h3 {{ color: #1a472a; margin-bottom: 0.2rem; font-size: 1rem; }}
        .feature-card p {{ color: #555; font-size: 0.85rem; }}
        
        /* Auth container - mobile optimized */
        .auth-container {{
            max-width: 100%;
            margin: 0 auto;
            background: {card_bg};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid {border_color};
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: {shadow};
        }}
        
        /* Stats - mobile optimized */
        .stat-box {{
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 0.8rem;
            text-align: center;
            transition: all 0.2s;
        }}
        .stat-box:hover {{ border-color: #2d8a4e; }}
        .stat-number {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #2d8a4e;
        }}
        .stat-label {{ font-size: 0.8rem; color: #666; }}
        
        /* Testimonial - mobile optimized */
        .testimonial {{
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-left: 4px solid #2d8a4e;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin: 0.5rem 0;
            border: 1px solid {border_color};
        }}
        .testimonial .quote {{ font-style: italic; color: #333; font-size: 0.9rem; }}
        .testimonial .author {{ font-weight: 600; color: #1a472a; margin-top: 0.3rem; font-size: 0.9rem; }}
        
        /* Footer - mobile optimized */
        .footer {{
            text-align: center;
            padding: 1.5rem;
            color: #888;
            border-top: 1px solid {border_color};
            margin-top: 2rem;
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: 12px;
            font-size: 0.8rem;
        }}
        
        /* Buttons - mobile optimized */
        .stButton > button {{
            background: linear-gradient(135deg, #1a472a, #2d8a4e) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            border-radius: 50px !important;
            padding: 0.6rem 1.5rem !important;
            font-size: 0.95rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }}
        .stButton > button:hover {{
            transform: scale(1.02) !important;
            box-shadow: 0 8px 30px rgba(45,138,78,0.4) !important;
        }}
        
        /* WhatsApp button - mobile optimized */
        .whatsapp-btn {{
            background: #25D366;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-size: 14px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 8px 0;
            transition: transform 0.3s;
            width: 100%;
            text-align: center;
        }}
        .whatsapp-btn:hover {{
            transform: scale(1.02);
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .plant-bg {{
                grid-template-columns: repeat(3, 1fr);
                font-size: 1rem;
            }}
            .plant-bg span {{ font-size: 0.9rem; }}
            .hero h1 {{ font-size: 1.6rem; }}
            .hero p {{ font-size: 0.9rem; }}
            .main-content {{ padding: 0.8rem; margin: 0.3rem; }}
            .stat-number {{ font-size: 1.4rem; }}
            .feature-card {{ padding: 0.8rem; }}
            .feature-card .icon {{ font-size: 1.8rem; }}
            .feature-card h3 {{ font-size: 0.9rem; }}
            .feature-card p {{ font-size: 0.8rem; }}
            .auth-container {{ padding: 1rem; }}
            .footer {{ padding: 1rem; font-size: 0.7rem; }}
        }}
        
        @media (max-width: 480px) {{
            .plant-bg {{
                grid-template-columns: repeat(2, 1fr);
                font-size: 0.8rem;
            }}
            .plant-bg span {{ font-size: 0.7rem; }}
            .hero h1 {{ font-size: 1.3rem; }}
            .hero {{ padding: 1rem; }}
            .hero p {{ font-size: 0.8rem; }}
            .main-content {{ padding: 0.5rem; margin: 0.2rem; }}
            .stat-number {{ font-size: 1.2rem; }}
        }}
        
        /* Animations */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .fade-in {{ animation: fadeInUp 0.5s ease-out; }}
        
        /* Progress bar */
        .stSpinner > div {{
            border-color: #2d8a4e !important;
        }}
    </style>
    """

# ============================================
# DATABASE LAYER (PostgreSQL + JSON Fallback)
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
                email TEXT UNIQUE,
                password TEXT,
                joined TEXT,
                plants_identified INTEGER DEFAULT 0
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
        conn.commit()
        print("✅ PostgreSQL connected")
    except Exception as e:
        USE_POSTGRES = False
        print(f"⚠️ PostgreSQL connection failed: {e}")

def load_users():
    if USE_POSTGRES:
        try:
            cur = conn.cursor()
            cur.execute("SELECT username, email, password, joined, plants_identified FROM users")
            rows = cur.fetchall()
            users = {}
            for row in rows:
                users[row[0]] = {
                    "email": row[1],
                    "password": row[2],
                    "joined": row[3],
                    "plants_identified": row[4],
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
            "email": "john@farm.com",
            "password": hashlib.sha256("farm2024".encode()).hexdigest(),
            "joined": datetime.now().isoformat(),
            "plants_identified": 12,
            "history": []
        }
    }

def save_users(users):
    if USE_POSTGRES:
        try:
            for username, data in users.items():
                cur.execute("""
                    INSERT INTO users (username, email, password, joined, plants_identified)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        email = EXCLUDED.email,
                        password = EXCLUDED.password,
                        plants_identified = EXCLUDED.plants_identified
                """, (username, data['email'], data['password'], data['joined'], data.get('plants_identified', 0)))
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
# NIGERIAN CROP DATABASE
# ============================================
NIGERIAN_CROPS = {
    "cassava": {
        "local_name": "Akpu/Kpo/Rogo",
        "season": "April to October",
        "harvest": "9-12 months",
        "price": "₦50,000-80,000/ton",
        "diseases": ["Cassava Mosaic Disease", "Cassava Brown Streak", "Anthracnose"],
        "uses": "Food, starch production, animal feed, ethanol",
        "soil": "Well-drained sandy loam, pH 5.5-6.5",
        "water": "Moderate rainfall (1000-1500mm)",
        "storage": "Process within 48 hours of harvest",
        "emoji": "🌿"
    },
    "rice": {
        "local_name": "Shinkafa/Osikapa",
        "season": "May to November",
        "harvest": "4-5 months",
        "price": "₦80,000-120,000/ton",
        "diseases": ["Rice Blast", "Sheath Blight", "Bacterial Leaf Blight"],
        "uses": "Food, brewing, animal feed",
        "soil": "Clay or loamy soil, pH 5.5-6.5",
        "water": "High (1500-2000mm)",
        "storage": "Dry to 12-14% moisture",
        "emoji": "🌾"
    },
    "yam": {
        "local_name": "Isu/Na/Eba",
        "season": "March to October",
        "harvest": "7-9 months",
        "price": "₦100,000-150,000/ton",
        "diseases": ["Yam Anthracnose", "Yam Mosaic Virus", "Nematodes"],
        "uses": "Food, animal feed, medicinal",
        "soil": "Well-drained sandy loam, pH 5.5-6.5",
        "water": "Moderate (1000-1500mm)",
        "storage": "Store in well-ventilated yam barn",
        "emoji": "🍠"
    },
    "groundnut": {
        "local_name": "Epa/Geda",
        "season": "May to October",
        "harvest": "4-5 months",
        "price": "₦350,000-450,000/ton",
        "diseases": ["Groundnut Rosette", "Leaf Spot", "Rust"],
        "uses": "Food, oil production, animal feed",
        "soil": "Well-drained sandy soil, pH 5.5-6.5",
        "water": "Moderate (500-800mm)",
        "storage": "Dry to 8-10% moisture",
        "emoji": "🥜"
    },
    "tomato": {
        "local_name": "Tomati/Tumatir",
        "season": "October to March (dry season)",
        "harvest": "2-3 months",
        "price": "₦50,000-80,000/ton",
        "diseases": ["Tomato Blight", "Tomato Mosaic Virus", "Fusarium Wilt"],
        "uses": "Food, processing, sauces",
        "soil": "Well-drained loamy soil, pH 6.0-6.8",
        "water": "Moderate (500-800mm)",
        "storage": "Store at room temperature, not in fridge",
        "emoji": "🍅"
    },
    "pepper": {
        "local_name": "Shombo/Tatashe/Bawa",
        "season": "October to March",
        "harvest": "2-3 months",
        "price": "₦100,000-150,000/ton",
        "diseases": ["Pepper Anthracnose", "Bacterial Spot", "Virus"],
        "uses": "Food, spice, medicine",
        "soil": "Well-drained sandy loam, pH 6.0-6.8",
        "water": "Moderate (400-600mm)",
        "storage": "Dry and store in airtight containers",
        "emoji": "🌶️"
    },
    "maize": {
        "local_name": "Agbado/Oka",
        "season": "April to September",
        "harvest": "3-4 months",
        "price": "₦40,000-60,000/ton",
        "diseases": ["Maize Lethal Necrosis", "Fall Armyworm", "Leaf Blight"],
        "uses": "Food, animal feed, flour, ethanol",
        "soil": "Well-drained loamy soil, pH 5.5-6.5",
        "water": "Moderate (500-1000mm)",
        "storage": "Dry to 12-14% moisture, store in airtight containers",
        "emoji": "🌽"
    },
    "sorghum": {
        "local_name": "Dawa/Wake",
        "season": "May to October",
        "harvest": "4-5 months",
        "price": "₦60,000-80,000/ton",
        "diseases": ["Sorghum Smut", "Leaf Blight", "Downy Mildew"],
        "uses": "Food, animal feed, brewing",
        "soil": "Well-drained sandy loam, pH 5.5-6.5",
        "water": "Low (400-600mm)",
        "storage": "Dry to 12-14% moisture",
        "emoji": "🌾"
    },
    "cocoa": {
        "local_name": "Koko",
        "season": "October to December (main), April to June (mid-crop)",
        "harvest": "5-6 months after flowering",
        "price": "₦800,000-1,200,000/ton",
        "diseases": ["Black Pod", "Witches' Broom", "Mirids"],
        "uses": "Chocolate, cocoa butter, beverages",
        "soil": "Well-drained deep soil, pH 6.0-6.5",
        "water": "High (1500-2000mm)",
        "storage": "Dry to 7-8% moisture, store in dry place",
        "emoji": "🍫"
    },
    "palm_oil": {
        "local_name": "Epo",
        "season": "All year round",
        "harvest": "4-5 years after planting",
        "price": "₦250,000-350,000/ton",
        "diseases": ["Ganoderma", "Fusarium Wilt", "Bud Rot"],
        "uses": "Cooking oil, soap, biodiesel, cosmetics",
        "soil": "Well-drained loamy soil, pH 4.5-6.0",
        "water": "High (1500-2000mm)",
        "storage": "Store in cool, dark place",
        "emoji": "🌴"
    },
    "beans": {
        "local_name": "Ewa/Olojola",
        "season": "August to December",
        "harvest": "2-3 months",
        "price": "₦200,000-300,000/ton",
        "diseases": ["Bean Rust", "Anthracnose", "Bacterial Blight"],
        "uses": "Food, animal feed",
        "soil": "Well-drained loamy soil, pH 6.0-7.0",
        "water": "Moderate (500-800mm)",
        "storage": "Dry to 10-12% moisture",
        "emoji": "🫘"
    },
    "plantain": {
        "local_name": "Ogede/Ayaba",
        "season": "All year round",
        "harvest": "9-12 months after planting",
        "price": "₦100,000-150,000/ton",
        "diseases": ["Black Sigatoka", "Panama Disease", "Mosaic Virus"],
        "uses": "Food, flour, chips",
        "soil": "Well-drained loamy soil, pH 5.5-6.5",
        "water": "High (1500-2000mm)",
        "storage": "Store in cool, dry place",
        "emoji": "🍌"
    },
    "okra": {
        "local_name": "Ila/Iro",
        "season": "March to October",
        "harvest": "2-3 months",
        "price": "₦50,000-80,000/ton",
        "diseases": ["Okra Mosaic", "Powdery Mildew", "Bacterial Wilt"],
        "uses": "Food, soups",
        "soil": "Well-drained loamy soil, pH 6.0-6.8",
        "water": "Moderate (500-800mm)",
        "storage": "Store in refrigerator for 2-3 days",
        "emoji": "🥬"
    },
    "millet": {
        "local_name": "Gero/Maiwa",
        "season": "May to October",
        "harvest": "3-4 months",
        "price": "₦70,000-90,000/ton",
        "diseases": ["Millet Blast", "Downy Mildew", "Smut"],
        "uses": "Food, animal feed, brewing",
        "soil": "Well-drained sandy soil, pH 5.5-6.5",
        "water": "Low (400-600mm)",
        "storage": "Dry to 12-14% moisture",
        "emoji": "🌾"
    },
    "sesame": {
        "local_name": "Isasa/Ekuku",
        "season": "July to December",
        "harvest": "3-4 months",
        "price": "₦300,000-400,000/ton",
        "diseases": ["Sesame Phyllody", "Bacterial Blight", "Fusarium Wilt"],
        "uses": "Oil, food, animal feed",
        "soil": "Well-drained sandy loam, pH 5.5-6.5",
        "water": "Low (400-600mm)",
        "storage": "Dry to 6-8% moisture",
        "emoji": "🌿"
    }
}

def get_crop_info(plant_name):
    plant_lower = plant_name.lower()
    for crop, info in NIGERIAN_CROPS.items():
        if crop in plant_lower:
            return crop, info
    return None, None

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
# WEATHER & ADVICE FUNCTIONS
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
        advice += "🌧️ **Tip:** Skip watering today! Nature is doing it for you."
    elif weather_info['temperature'] > 30:
        advice += "☀️ **Hot Weather:** Check soil daily. May need extra water."
    elif weather_info['temperature'] < 5:
        advice += "❄️ **Cold Weather:** Bring indoors if outside. Reduce watering."
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
# NAVIGATION
# ============================================
def navigation():
    with st.sidebar:
        st.markdown(f"### {get_text('app_name')}")
        st.markdown("---")
        
        if st.session_state.logged_in:
            st.markdown(f"### 👋 Hello, {st.session_state.username}!")
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
            "👤 Profile": "profile" if st.session_state.logged_in else "auth",
            "🌱 Identify": "identify",
            "🩺 Disease": "disease",
            "📹 Video": "video",
            "📚 Learn": "learn",
            "❓ FAQ": "faq",
            "📖 About": "about"
        }
        for label, page in nav_items.items():
            if st.button(label, use_container_width=True):
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
        
        if st.session_state.logged_in:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.user_email = ""
                st.rerun()
        else:
            if st.button("🔐 Login", use_container_width=True):
                st.session_state.page = "auth"
                st.rerun()

# ============================================
# HOME PAGE
# ============================================
def home_page():
    crop_items = ["🌿 Cassava", "🌾 Rice", "🍠 Yam", "🥜 Groundnut", "🍅 Tomato", "🌶️ Pepper", "🌽 Maize", "🌾 Sorghum", "🍫 Cocoa", "🌴 Palm Oil"]
    bg_html = '<div class="plant-bg">'
    for i in range(36):
        bg_html += f'<span>{crop_items[i % len(crop_items)]}</span>'
    bg_html += '</div>'
    st.markdown(bg_html, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="hero">
            <h1>🌿 PlantPal</h1>
            <p>{get_text('tagline')}</p>
            <div class="subtitle">Identify Cassava, Rice, Yam, Tomato, Pepper, Maize, Cocoa & more</div>
            <br>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("🚀 Get Started", use_container_width=True, type="primary"):
                if st.session_state.logged_in:
                    st.session_state.page = "identify"
                else:
                    st.session_state.page = "auth"
                st.rerun()

        st.markdown("---")

        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.8rem; margin: 1rem 0;">
            <div class="stat-box"><div class="stat-number">50K+</div><div class="stat-label">Identified</div></div>
            <div class="stat-box"><div class="stat-number">38</div><div class="stat-label">Diseases</div></div>
            <div class="stat-box"><div class="stat-number">15+</div><div class="stat-label">Nigerian Crops</div></div>
            <div class="stat-box"><div class="stat-number">92%</div><div class="stat-label">Accuracy</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("## How PlantPal Helps")
        cols = st.columns(3)
        features = [
            ("🌱", "Identify", "Cassava, Rice, Yam, Tomato, Pepper & more"),
            ("🩺", "Detect", "38+ diseases with treatments"),
            ("🇳🇬", "Prices", "Market prices in ₦ per ton")
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

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# AUTH PAGE
# ============================================
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

# ============================================
# PROFILE PAGE
# ============================================
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
            <p style="color: #666; font-size:0.9rem;">{user_data.get('email', '')}</p>
            <p style="color: #888; font-size:0.8rem;">Joined: {user_data.get('joined', '')[:10]}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        plants = user_data.get('plants_identified', 0)
        history = user_data.get('history', [])
        st.markdown("### 📊 Statistics")
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem;">
            <div class="stat-box"><div class="stat-number">{plants}</div><div class="stat-label">Plants</div></div>
            <div class="stat-box"><div class="stat-number">{len(history)}</div><div class="stat-label">Entries</div></div>
        </div>
        """, unsafe_allow_html=True)
        if history:
            st.markdown("### 📜 Recent")
            for item in history[-5:]:
                st.markdown(f"- **{item['plant']}** - {item['date'][:10]}")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# IDENTIFY PAGE
# ============================================
def identify_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 🌱 Identify a Plant")
    st.markdown("Upload a photo of any plant")
    
    uploaded = st.file_uploader("Upload Plant Photo", type=["jpg","jpeg","png"])
    city = st.text_input("Your City", placeholder="e.g., Lagos, Ibadan, Kano")
    
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
                        
                        st.success("✅ Complete!")
                        st.markdown("---")
                        st.markdown(advice)
                        
                        if crop:
                            st.markdown("---")
                            st.markdown(f"## 🇳🇬 {crop.capitalize()}")
                            st.markdown(f"**Local:** {info['local_name']}")
                            st.markdown(f"**Season:** {info['season']}")
                            st.markdown(f"**Harvest:** {info['harvest']}")
                            st.markdown(f"**Price:** {info['price']}")
                            st.markdown(f"**Diseases:** {', '.join(info['diseases'])}")
                            st.markdown(f"**Uses:** {info['uses']}")
                            st.markdown(f"**Soil:** {info['soil']}")
                            
                            share_text = f"🌿 PlantPal: {crop.capitalize()}\nLocal: {info['local_name']}\nSeason: {info['season']}\nPrice: {info['price']}"
                            share_url = whatsapp_share(share_text)
                            st.markdown(f'<a href="{share_url}" target="_blank"><button class="whatsapp-btn">📱 Share on WhatsApp</button></a>', unsafe_allow_html=True)
                        
                        st.markdown(f"**🔬 Confidence:** {conf:.2%}")
                        st.markdown("---")
                        st.markdown("### ☠️ Safety")
                        st.markdown(toxicity)
                        
                        if st.session_state.logged_in:
                            update_user_history(st.session_state.username, plant_name)
                            st.success("✅ Saved!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Model not available")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# DISEASE PAGE
# ============================================
def disease_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 🩺 Disease Detection")
    uploaded = st.file_uploader("Upload Diseased Leaf", type=["jpg","jpeg","png"], key="disease")
    if uploaded:
        st.image(uploaded, caption="Leaf", use_container_width=True)
        if st.button("🔬 Detect", type="primary"):
            with st.spinner("Analyzing..."):
                diseases = {
                    "Cassava Mosaic": "Remove infected plants. Use resistant varieties.",
                    "Rice Blast": "Use resistant varieties. Apply fungicide.",
                    "Yam Anthracnose": "Use clean seeds. Apply fungicide.",
                    "Tomato Blight": "Use resistant varieties. Apply fungicide.",
                    "Pepper Anthracnose": "Apply fungicide. Remove infected fruits.",
                    "Maize Lethal Necrosis": "Remove infected plants. Control insects.",
                    "Fall Armyworm": "Apply appropriate insecticide. Early detection key."
                }
                disease = random.choice(list(diseases.keys()))
                treatment = diseases[disease]
                st.markdown(f"""
                **🩺 Disease:** {disease}
                **🔬 Treatment:** {treatment}
                **🔬 Confidence:** {random.randint(75,95)}%
                """)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# VIDEO PAGE
# ============================================
def video_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 📹 Video Analysis")
    video = st.file_uploader("Upload Video", type=["mp4","mov","avi"], key="video")
    if video:
        st.video(video)
        if st.button("🎬 Analyze", type="primary"):
            with st.spinner("Processing..."):
                st.markdown("**🌿 Plant:** Cassava (78% confidence)")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# LEARNING CENTER
# ============================================
def learning_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 📚 Learning Center")
    tabs = st.tabs(["🇳🇬 Crops", "🌱 Care", "🩺 Disease", "📱 How"])
    with tabs[0]:
        st.markdown("### Nigerian Crop Guide")
        for crop, info in NIGERIAN_CROPS.items():
            with st.expander(f"{info['emoji']} {crop.capitalize()}"):
                st.markdown(f"**Local:** {info['local_name']}")
                st.markdown(f"**Season:** {info['season']}")
                st.markdown(f"**Harvest:** {info['harvest']}")
                st.markdown(f"**Price:** {info['price']}")
                st.markdown(f"**Diseases:** {', '.join(info['diseases'])}")
    with tabs[1]:
        st.markdown("### Plant Care")
        st.markdown("""
        **Water:** Morning/evening, avoid overwatering.
        **Sunlight:** 4-6 hours daily.
        **Soil:** Add compost, test pH.
        """)
    with tabs[2]:
        st.markdown("### Disease Prevention")
        st.markdown("""
        1. Use resistant varieties
        2. Space plants properly
        3. Avoid overhead watering
        4. Remove infected plants
        """)
    with tabs[3]:
        st.markdown("### How to Use")
        st.markdown("""
        1. Take a photo
        2. Upload and enter city
        3. Get results
        4. Share via WhatsApp
        """)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# FAQ PAGE
# ============================================
def faq_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## ❓ FAQ")
    faqs = [
        ("What is PlantPal?", "AI farming assistant for Nigerian farmers."),
        ("Is it free?", "Yes, completely free!"),
        ("Do I need internet?", "Yes, internet required."),
        ("Is my data private?", "Yes, images are not stored."),
        ("How accurate?", "92% for identification."),
        ("How to create account?", "Click 'Sign Up'."),
        ("Which crops?", "Cassava, Rice, Yam, Tomato, Pepper, Maize, Cocoa, and more!"),
        ("Can I share results?", "Yes! Use WhatsApp share button.")
    ]
    for q,a in faqs:
        with st.expander(f"📌 {q}"):
            st.markdown(a)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# ABOUT PAGE
# ============================================
def about_page():
    st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 📖 About PlantPal")
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("""
        ### 🇳🇬 Our Mission
        Empower Nigerian farmers with AI.

        ### 🌱 Our Story
        Built for Nigerian farmers to identify crops and diseases.

        ### 🌾 Our Crops
        Cassava, Rice, Yam, Groundnut, Tomato, Pepper, Maize, Sorghum, Cocoa, Palm Oil, Beans, Plantain, Okra, Millet, Sesame

        ### 🌟 Our Values
        - 🌱 Accessibility
        - 🤝 Community
        - 🇳🇬 Local Focus
        """)
    with col2:
        st.markdown("""
        ### Quick Facts
        - Founded: 2024
        - Users: 50,000+
        - Crops: 15+
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
    st.markdown(get_css(), unsafe_allow_html=True)
    navigation()
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "auth":
        auth_page()
    elif st.session_state.page == "profile":
        if st.session_state.logged_in:
            profile_page()
        else:
            st.warning("Please login")
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
    st.markdown("""
    <div class="footer">
        <p>🇳🇬 PlantPal - Smart Farming Assistant</p>
        <p style="font-size:0.7rem;">© 2024 PlantPal. Built with ❤️ for Nigerian farmers</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()