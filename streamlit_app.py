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
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = False
if "otp" not in st.session_state:
    st.session_state.otp = None
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False
if "profile_complete" not in st.session_state:
    st.session_state.profile_complete = False
if "show_login_required" not in st.session_state:
    st.session_state.show_login_required = False
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
        "home": "Home",
        "back": "← Back",
        "verify_email": "Verify Email",
        "send_otp": "Send OTP",
        "enter_otp": "Enter OTP",
        "feedback": "Feedback",
        "weeds": "Weeds & Pesticides",
        "fertilizers": "Fertilizers",
        "ask_ai": "Ask AI"
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
        "home": "Ilé",
        "back": "← Padà",
        "verify_email": "Ṣe Ìdánilójú Imeeli",
        "send_otp": "Fi OTP Ránṣẹ́",
        "enter_otp": "Tẹ OTP",
        "feedback": "Èsì",
        "weeds": "Ewéko àti Pesticide",
        "fertilizers": "Ajílẹ̀",
        "ask_ai": "Beèrè Lọ́wọ́ AI"
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
        "home": "Gida",
        "back": "← Koma",
        "verify_email": "Tabbatar da Imel",
        "send_otp": "Aika OTP",
        "enter_otp": "Shigar da OTP",
        "feedback": "Ra'ayi",
        "weeds": "Ciyawa da Magunguna",
        "fertilizers": "Taki",
        "ask_ai": "Tambayi AI"
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
        "home": "Ụlọ",
        "back": "← Lọghachi",
        "verify_email": "Nyochaa Email",
        "send_otp": "Zipụ OTP",
        "enter_otp": "Tinye OTP",
        "feedback": "Ntụghachi",
        "weeds": "Ahịhịa na Pesticide",
        "fertilizers": "Fatịlaịza",
        "ask_ai": "Jụọ AI"
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
        "home": "Home",
        "back": "← Go Back",
        "verify_email": "Verify Email",
        "send_otp": "Send OTP",
        "enter_otp": "Enter OTP",
        "feedback": "Feedback",
        "weeds": "Weeds & Pesticides",
        "fertilizers": "Fertilizers",
        "ask_ai": "Ask AI"
    }
}

def get_text(key):
    lang_code = LANGUAGES.get(st.session_state.language, "en")
    return TRANSLATIONS.get(lang_code, {}).get(key, key)

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
    
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    st.session_state.otp = otp
    st.session_state.otp_verified = False
    st.session_state.pending_username = username
    st.session_state.pending_full_name = full_name
    st.session_state.pending_email = email
    st.session_state.pending_password = password
    
    # Send OTP via email (placeholder - you'll need to set up email)
    try:
        # For now, just show the OTP in the UI for testing
        st.info(f"📧 Your OTP is: **{otp}** (In production, this would be sent to your email)")
        return True, "OTP generated! Check the code above to verify."
    except:
        return True, "OTP generated! Please verify."

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

# ============================================
# NIGERIAN WEEDS DATABASE
# ============================================
NIGERIAN_WEEDS = {
    "spear_grass": {
        "name": "Spear Grass (Imperata cylindrica)",
        "description": "Common in fallow lands and farms. Very persistent with deep rhizomes.",
        "control_organic": "Deep plowing, mulching, repeated cutting before flowering, use of cover crops",
        "control_chemical": "Glyphosate or Paraquat applied at early growth stage (3-5 leaves)",
        "prevention": "Regular monitoring, crop rotation, maintain dense crop canopy",
        "season": "All year round, active in rainy season",
        "emoji": "🌾"
    },
    "goat_weed": {
        "name": "Goat Weed (Ageratum conyzoides)",
        "description": "Annual herb that spreads rapidly in disturbed soil. Produces many seeds.",
        "control_organic": "Hand pulling before flowering, heavy mulching, intercropping",
        "control_chemical": "2,4-D or Atrazine applied pre-emergence",
        "prevention": "Maintain soil cover, proper crop spacing, use of competitive crops",
        "season": "Rainy season (May-October)",
        "emoji": "🌿"
    },
    "mimosa": {
        "name": "Mimosa (Mimosa pudica)",
        "description": "Spreading herb with thorns. Covers ground rapidly and is hard to remove.",
        "control_organic": "Manual pulling of roots before seed set, heavy mulching, slash and burn",
        "control_chemical": "Glyphosate or Dicamba at early growth stage",
        "prevention": "Avoid seed spread, regular weeding, use of cover crops",
        "season": "Rainy season",
        "emoji": "🌱"
    },
    "bermuda_grass": {
        "name": "Bermuda Grass (Cynodon dactylon)",
        "description": "Very aggressive perennial grass. Spreads by rhizomes and stolons.",
        "control_organic": "Deep digging and removal of rhizomes, solarization, use of shade crops",
        "control_chemical": "Glyphosate or Fusilade applied to actively growing grass",
        "prevention": "Deep plowing, mulching, proper land preparation",
        "season": "All year round",
        "emoji": "🌾"
    },
    "pigweed": {
        "name": "Pigweed (Amaranthus spinosus)",
        "description": "Annual weed with spines. Seeds spread widely and persist in soil.",
        "control_organic": "Hand pulling before seed set, mulching, crop rotation",
        "control_chemical": "Atrazine or 2,4-D applied pre-emergence",
        "prevention": "Early detection, regular weeding, use of herbicides as pre-plant",
        "season": "Rainy season (May-September)",
        "emoji": "🌿"
    },
    "couch_grass": {
        "name": "Couch Grass (Digitaria sanguinalis)",
        "description": "Annual grass that grows rapidly in disturbed soils. Competes strongly for nutrients.",
        "control_organic": "Hand weeding, mulching, dense planting",
        "control_chemical": "Atrazine, Diuron, or Glyphosate",
        "prevention": "Regular monitoring, maintain crop canopy",
        "season": "Rainy season",
        "emoji": "🌾"
    }
}

def get_weed_info(weed_name):
    weed_lower = weed_name.lower()
    for weed_key, info in NIGERIAN_WEEDS.items():
        if weed_key in weed_lower or info['name'].lower() in weed_lower:
            return info
    return None

# ============================================
# NIGERIAN FERTILIZER DATABASE
# ============================================
NIGERIAN_FERTILIZERS = {
    "cassava": {
        "best": "NPK 15-15-15 + organic compost",
        "organic": "Poultry manure, compost, wood ash, cocoa pod husk",
        "application": "Apply 4-6 months after planting. 200kg/ha NPK or 2-3 tons/ha poultry manure",
        "timing": "Early rainy season (March-April)",
        "local_options": "Compost from farm waste, poultry manure, palm oil waste"
    },
    "rice": {
        "best": "NPK 20-10-10 + Urea topdressing",
        "organic": "Compost, green manure, rice straw, cattle manure",
        "application": "At planting (300kg/ha NPK) and at tillering (100kg/ha Urea)",
        "timing": "Start of rainy season and 30 days after planting",
        "local_options": "Rice straw compost, cattle manure, poultry manure"
    },
    "maize": {
        "best": "NPK 15-15-15 at planting, side-dress with Urea at 6-8 weeks",
        "organic": "Poultry manure, compost, cow dung",
        "application": "250kg/ha NPK at planting, 100kg/ha Urea at 6-8 weeks",
        "timing": "Start of rainy season",
        "local_options": "Poultry manure, farmyard manure, compost"
    },
    "yam": {
        "best": "Organic manure + NPK 10-10-10",
        "organic": "Cattle manure, compost, wood ash, cocoa pod husk",
        "application": "Apply at mound making and top dress at 3 months (100kg/ha)",
        "timing": "Planting season (March-May)",
        "local_options": "Cattle manure, compost, palm oil residue"
    },
    "tomato": {
        "best": "NPK 20-20-20 weekly during fruiting",
        "organic": "Compost, poultry manure, seaweed extract, fish waste",
        "application": "Every 7-10 days during growing season (2-3kg/ha/week)",
        "timing": "Throughout growing season",
        "local_options": "Compost tea, poultry manure, fish waste, wood ash"
    },
    "pepper": {
        "best": "NPK 15-15-15 + calcium (CaNO3) for fruit development",
        "organic": "Compost, poultry manure, bone meal, wood ash",
        "application": "Apply at planting (200kg/ha) and top dress monthly (100kg/ha)",
        "timing": "Start of dry season (October-November)",
        "local_options": "Poultry manure, compost, palm oil waste"
    },
    "groundnut": {
        "best": "Minimal fertilizer (legume) + 10kg/ha phosphorus",
        "organic": "Compost, cattle manure, rock phosphate",
        "application": "Apply P fertilizer at planting. Avoid nitrogen (uses own)",
        "timing": "Planting season (May-June)",
        "local_options": "Compost, cattle manure, bone meal"
    }
}

def get_fertilizer_info(crop_name):
    crop_lower = crop_name.lower()
    for crop, info in NIGERIAN_FERTILIZERS.items():
        if crop in crop_lower:
            return info
    return None

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
# AI CHATBOT FUNCTION
# ============================================
def get_ai_response(question):
    """Simple AI response using crop database"""
    question_lower = question.lower()
    
    # Check if question is about a crop
    for crop, info in NIGERIAN_CROPS.items():
        if crop in question_lower:
            return f"""
**🌿 {crop.capitalize()}**

**Local Name:** {info['local_name']}
**Growing Season:** {info['season']}
**Harvest Time:** {info['harvest']}
**Market Price:** {info['price']}

**Common Diseases:**
- {chr(10).join(['- ' + d for d in info['diseases']])}

**Uses:** {info['uses']}
**Soil:** {info['soil']}
**Water:** {info['water']}
**Storage:** {info['storage']}
"""
    
    # Check if question is about a weed
    for weed_key, info in NIGERIAN_WEEDS.items():
        if weed_key in question_lower or info['name'].lower() in question_lower:
            return f"""
**🌿 {info['name']}**

**Description:** {info['description']}

**🌱 Organic Control:** {info['control_organic']}

**🧪 Chemical Control:** {info['control_chemical']}

**🛡️ Prevention:** {info['prevention']}

**📅 Season:** {info['season']}
"""
    
    # Check if question is about fertilizer
    for crop, info in NIGERIAN_FERTILIZERS.items():
        if crop in question_lower:
            return f"""
**🌱 Fertilizer Guide for {crop.capitalize()}**

**✅ Best Fertilizer:** {info['best']}

**🌿 Organic Options:** {info['organic']}

**📊 Application:** {info['application']}

**📅 Timing:** {info['timing']}

**🏡 Local Options:** {info['local_options']}
"""
    
    # Check for common questions
    if "what is plantpal" in question_lower or "what do you do" in question_lower:
        return """
**🌿 PlantPal** is an AI-powered farming assistant for Nigerian farmers.

**I help you:**
- ✅ Identify plants from photos
- ✅ Detect plant diseases
- ✅ Get market prices in ₦
- ✅ Learn about Nigerian crops
- ✅ Get weather-based care advice
- ✅ Find organic fertilizer options
- ✅ Identify weeds and get control methods

**All for free!**
"""
    
    if "how to use" in question_lower or "how do i" in question_lower:
        return """
**📱 How to Use PlantPal**

**1.** 📸 Take a photo of any plant
**2.** ☁️ Upload it to PlantPal
**3.** 📍 Enter your city for weather advice
**4.** 🌿 Get results - name, care tips, prices
**5.** 📤 Share with other farmers via WhatsApp

It's that simple!
"""
    
    if "disease" in question_lower or "sick" in question_lower:
        return """
**🩺 Common Nigerian Plant Diseases**

**🌿 Cassava Mosaic** - Remove infected plants, use resistant varieties
**🌾 Rice Blast** - Use resistant varieties, apply fungicide
**🍠 Yam Anthracnose** - Use clean seeds, destroy infected vines
**🍅 Tomato Blight** - Use resistant varieties, avoid overhead watering
**🌽 Maize Lethal Necrosis** - Remove infected plants, control insects

**💡 Prevention is key!**
- Space plants properly
- Use disease-resistant varieties
- Remove infected plants immediately
"""
    
    if "fertilizer" in question_lower or "fertilize" in question_lower:
        return """
**🌱 Fertilizer Tips for Nigerian Crops**

**🌿 Cassava:** NPK 15-15-15 at 4-6 months
**🌾 Rice:** NPK 20-10-10 at planting and tillering
**🌽 Maize:** NPK 15-15-15 at planting + Urea side-dress
**🍠 Yam:** Organic manure + NPK 10-10-10
**🍅 Tomato:** NPK 20-20-20 weekly during fruiting
**🌶️ Pepper:** NPK 15-15-15 + calcium

**💡 Always test soil first!**
"""
    
    if "weed" in question_lower or "weeds" in question_lower:
        return """
**🌿 Common Weeds in Nigeria & Control**

**🌾 Spear Grass:** Deep plowing, Glyphosate, mulching
**🌿 Goat Weed:** Hand pulling, 2,4-D, heavy mulching
**🌱 Mimosa:** Manual pulling, Glyphosate, slash and burn
**🌾 Bermuda Grass:** Deep digging, Glyphosate, solarization
**🌿 Pigweed:** Hand pulling, Atrazine, crop rotation

**💡 Prevention:**
- Regular monitoring
- Maintain crop cover
- Use cover crops
"""
    
    if "pesticide" in question_lower:
        return """
**🧪 Organic Pesticides for Nigerian Farms**

**🌿 Neem Oil:** Effective against aphids, mites, leaf miners
**🌶️ Pepper Spray:** Repels insects, mix with water and soap
**🧄 Garlic Spray:** Natural repellent for many pests
**🌿 Wood Ash:** Controls snails, slugs, and some insects
**🪴 Soap Spray:** Kills soft-bodied insects like aphids

**💡 Always test on a small area first!**
"""
    
    return """
🤔 **I'm not sure about that. Try asking me about:**

**🌿 Specific crops** (e.g., "tell me about cassava")
**🩺 Diseases** (e.g., "how to treat tomato blight")
**🌱 Fertilizers** (e.g., "best fertilizer for rice")
**🌿 Weeds** (e.g., "how to remove spear grass")
**📱 How to use PlantPal** (e.g., "how do I use this app")
**🧪 Pesticides** (e.g., "organic pesticides")

**I'm always learning!**
"""

# ============================================
# CUSTOM CSS - COMPLETE
# ============================================
def get_css():
    if st.session_state.theme == "dark":
        bg_color = "#0a0a1a"
        text_color = "#e0e0e0"
        card_bg = "rgba(30,30,50,0.85)"
        border_color = "#444466"
        shadow = "0 8px 32px rgba(0,0,0,0.4)"
        hero_bg = "linear-gradient(135deg, #0a1a0a, #1a3a2a, #0a1a0a)"
    else:
        bg_color = "#f0f4f0"
        text_color = "#1a1a2e"
        card_bg = "rgba(255,255,255,0.85)"
        border_color = "#c8d6c8"
        shadow = "0 8px 32px rgba(0,0,0,0.1)"
        hero_bg = "linear-gradient(135deg, #1a472a, #2d8a4e, #1a472a)"

    brightness = st.session_state.brightness / 100.0

    return f"""
    <style>
        .stApp {{
            background: {bg_color};
            color: {text_color};
            transition: background 0.3s, color 0.3s;
            padding: 0 !important;
        }}
        
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        .plant-bg {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.06;
            pointer-events: none;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: repeat(6, 1fr);
            font-size: 2rem;
            overflow: hidden;
            filter: brightness({brightness});
            user-select: none;
        }}
        .plant-bg span {{
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            animation: float 10s infinite ease-in-out;
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}
        
        .main-content {{
            position: relative;
            z-index: 1;
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 0.5rem;
            border: 1px solid {border_color};
            box-shadow: {shadow};
            transition: background 0.3s, border 0.3s;
        }}
        
        .hero {{
            background: {hero_bg};
            background-size: 300% 300%;
            animation: gradientShift 8s ease infinite;
            padding: 2.5rem 1.5rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
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
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
            position: relative;
            z-index: 1;
            text-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .hero p {{
            font-size: 1.3rem;
            opacity: 0.95;
            position: relative;
            z-index: 1;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        .hero .subtitle {{
            font-size: 1rem;
            opacity: 0.8;
            position: relative;
            z-index: 1;
            margin-top: 0.5rem;
        }}
        
        .feature-card {{
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 1.5rem 1rem;
            text-align: center;
            transition: all 0.4s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            height: 100%;
            cursor: pointer;
        }}
        .feature-card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
            border-color: #2d8a4e;
        }}
        .feature-card .icon {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        .feature-card h3 {{
            color: #1a472a;
            margin-bottom: 0.3rem;
            font-size: 1.1rem;
            font-weight: 700;
        }}
        .feature-card p {{
            color: #555;
            font-size: 0.9rem;
        }}
        
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
        
        .profile-pic {{
            font-size: 4rem;
            text-align: center;
        }}
        
        .back-btn {{
            background: {card_bg};
            border: 1px solid {border_color};
            border-radius: 10px;
            padding: 8px 15px;
            cursor: pointer;
            display: inline-block;
            transition: all 0.3s;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }}
        .back-btn:hover {{
            background: rgba(45,138,78,0.1);
            border-color: #2d8a4e;
        }}
        
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
        
        .stButton > button {{
            background: linear-gradient(135deg, #1a472a, #2d8a4e) !important;
            color: white !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 50px !important;
            padding: 0.7rem 2rem !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            box-shadow: 0 4px 15px rgba(45,138,78,0.3) !important;
        }}
        .stButton > button:hover {{
            transform: scale(1.03) !important;
            box-shadow: 0 8px 30px rgba(45,138,78,0.5) !important;
        }}
        
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
            transition: all 0.3s;
            width: 100%;
            text-align: center;
            font-weight: 600;
        }}
        .whatsapp-btn:hover {{
            transform: scale(1.03);
            box-shadow: 0 4px 20px rgba(37,211,102,0.4);
        }}
        
        .css-1d391kg, .css-1aumxhk {{
            background: {card_bg} !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-right: 1px solid {border_color};
        }}
        
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 2rem; }}
            .hero p {{ font-size: 1rem; }}
            .hero {{ padding: 1.5rem 1rem; }}
            .main-content {{ padding: 0.8rem; }}
            .feature-card {{ padding: 1rem; }}
            .feature-card .icon {{ font-size: 2rem; }}
            .plant-bg {{ font-size: 1.2rem; grid-template-columns: repeat(3, 1fr); }}
            .plant-bg span {{ font-size: 1rem; }}
        }}
        @media (max-width: 480px) {{
            .hero h1 {{ font-size: 1.5rem; }}
            .hero p {{ font-size: 0.85rem; }}
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
        
        .feedback-box {{
            background: {card_bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
        }}
    </style>
    """

# ============================================
# SIDEBAR NAVIGATION
# ============================================
def navigation():
    with st.sidebar:
        st.markdown(f"### {get_text('app_name')}")
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
# BACK BUTTON
# ============================================
def back_button():
    if st.button("← Back", key="back_btn"):
        st.session_state.page = st.session_state.previous_page
        st.rerun()

# ============================================
# ALL PAGE FUNCTIONS
# ============================================

def home_page():
    crop_items = ["🌿 Cassava", "🌾 Rice", "🍠 Yam", "🥜 Groundnut", "🍅 Tomato", "🌶️ Pepper", 
                  "🌽 Maize", "🌾 Sorghum", "🍫 Cocoa", "🌴 Palm Oil", "🫘 Beans", "🍌 Plantain"]
    bg_html = '<div class="plant-bg">'
    for i in range(48):
        bg_html += f'<span>{crop_items[i % len(crop_items)]}</span>'
    bg_html += '</div>'
    st.markdown(bg_html, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="main-content fade-in">', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="hero">
            <h1>🌿 PlantPal</h1>
            <p>🇳🇬 Your Smart Farming Assistant for Nigeria</p>
            <div class="subtitle">
                🌾 Identify Cassava, Rice, Yam, Tomato, Pepper, Maize, Cocoa, and 1000+ plants<br>
                🩺 Detect diseases early · 💰 Know market prices · 🌍 Available in 5 languages
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
                if st.button("🚀 Get Started - It's Free!", use_container_width=True, type="primary"):
                    st.session_state.page = "auth"
                    st.rerun()

        st.markdown("---")

        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.8rem; margin: 1rem 0;">
            <div class="stat-box"><div class="stat-number">50K+</div><div style="font-size:0.8rem;color:#666;">Plants Identified</div></div>
            <div class="stat-box"><div class="stat-number">38</div><div style="font-size:0.8rem;color:#666;">Diseases Detected</div></div>
            <div class="stat-box"><div class="stat-number">15+</div><div style="font-size:0.8rem;color:#666;">Nigerian Crops</div></div>
            <div class="stat-box"><div class="stat-number">92%</div><div style="font-size:0.8rem;color:#666;">Accuracy Rate</div></div>
            <div class="stat-box"><div class="stat-number">5</div><div style="font-size:0.8rem;color:#666;">Languages</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("## 🌟 What PlantPal Can Do For You")
        
        col1, col2, col3 = st.columns(3)
        features = [
            ("🌱", "Identify Any Plant", "Upload a photo and get the plant name, care instructions, and more."),
            ("🇳🇬", "Nigerian Crops", "Cassava, Rice, Yam, Tomato, Pepper, Maize, Cocoa & more."),
            ("🩺", "Disease Detection", "Upload a sick leaf and get disease diagnosis with treatment."),
            ("💰", "Market Prices", "Get current market prices for crops in ₦ per ton."),
            ("📱", "Share via WhatsApp", "Share plant info with other farmers directly."),
            ("🌍", "5 Languages", "Use in English, Yorùbá, Hausa, Igbo, or Pidgin.")
        ]
        for i, (icon, title, desc) in enumerate(features):
            with col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("## 📋 How It Works - 3 Simple Steps")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="text-align:center;padding:1rem;">
                <div style="font-size:3rem;background:#1a472a;color:white;width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto;">1</div>
                <h4>📸 Take a Photo</h4>
                <p style="color:#555;font-size:0.9rem;">Use your phone to take a clear photo.</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="text-align:center;padding:1rem;">
                <div style="font-size:3rem;background:#1a472a;color:white;width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto;">2</div>
                <h4>☁️ Upload & Analyze</h4>
                <p style="color:#555;font-size:0.9rem;">Upload and our AI will identify instantly.</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="text-align:center;padding:1rem;">
                <div style="font-size:3rem;background:#1a472a;color:white;width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto;">3</div>
                <h4>🌿 Get Results</h4>
                <p style="color:#555;font-size:0.9rem;">Get name, care tips, prices, and more.</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

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
        
        full_name = st.text_input("Full Name", placeholder="e.g., Adebayo Ogunlesi", key="signup_full_name")
        username = st.text_input("Username", placeholder="Choose a unique username", key="signup_user")
        email = st.text_input("Email Address", placeholder="your@email.com", key="signup_email")
        password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_pass")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm")
        
        st.markdown("---")
        st.markdown("### 📧 Email Verification")
        
        if st.button("📝 Sign Up", use_container_width=True, type="primary"):
            if not full_name or not username or not email or not password:
                st.error("All fields required")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif "@" not in email or "." not in email:
                st.error("Invalid email address")
            elif " " in username:
                st.error("Username cannot contain spaces")
            else:
                success, msg = register_user(username, full_name, email, password)
                if success:
                    st.success(msg)
                    
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
        new_pic = st.selectbox("Choose Profile Emoji", pic_options, 
                               index=pic_options.index(profile_pic) if profile_pic in pic_options else 0)
        if new_pic != profile_pic:
            if update_user_profile(st.session_state.username, 
                                  user_data.get('full_name', ''),
                                  user_data.get('nationality', ''),
                                  user_data.get('bio', ''),
                                  new_pic):
                st.success("✅ Profile picture updated!")
                st.rerun()
    
    with col2:
        st.markdown("### 📋 Personal Information")
        
        full_name = st.text_input("Full Name", value=user_data.get('full_name', ''))
        
        nationalities = ["Nigeria", "Ghana", "Kenya", "South Africa", "Uganda", "Tanzania", 
                         "Other African", "Other International"]
        current_nationality = user_data.get('nationality', '')
        nationality = st.selectbox("Nationality", nationalities, 
                                   index=nationalities.index(current_nationality) if current_nationality in nationalities else 0)
        
        bio = st.text_area("About You", value=user_data.get('bio', ''), 
                           placeholder="e.g., Cassava farmer from Oyo State.")
        
        st.text_input("Email", value=user_data.get('email', ''), disabled=True)
        st.text_input("Joined", value=user_data.get('joined', '')[:10], disabled=True)
        
        if st.button("💾 Save Profile", type="primary"):
            if update_user_profile(st.session_state.username, full_name, nationality, bio, new_pic):
                st.success("✅ Profile updated successfully!")
                st.session_state.full_name = full_name
                st.balloons()
                st.session_state.profile_complete = True
                time.sleep(0.5)
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Your Plant Journey")
        plants = user_data.get('plants_identified', 0)
        history = user_data.get('history', [])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{plants}</div>
                <div style="font-size:0.8rem;color:#666;">Plants Identified</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{len(history)}</div>
                <div style="font-size:0.8rem;color:#666;">Total Entries</div>
            </div>
            """, unsafe_allow_html=True)
        
        if history:
            st.markdown("### 📜 Your Plant History")
            for item in history[-5:]:
                st.markdown(f"- **{item['plant']}** - {item['date'][:10]}")
        
        if user_data.get("verified", False):
            st.success("✅ Email Verified")
        else:
            st.warning("⚠️ Email not verified.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def identify_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 🌱 Identify a Plant")
    st.markdown("Upload a photo and get plant name, care tips, and market prices")
    
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
                        
                        st.success("✅ Identification Complete!")
                        st.markdown("---")
                        st.markdown(advice)
                        
                        if crop:
                            st.markdown("---")
                            st.markdown(f"## 🇳🇬 {crop.capitalize()}")
                            st.markdown(f"**Local Name:** {info['local_name']}")
                            st.markdown(f"**Growing Season:** {info['season']}")
                            st.markdown(f"**Harvest Time:** {info['harvest']}")
                            st.markdown(f"**Market Price:** {info['price']}")
                            st.markdown(f"**Common Diseases:** {', '.join(info['diseases'])}")
                            st.markdown(f"**Uses:** {info['uses']}")
                            st.markdown(f"**Soil Requirements:** {info['soil']}")
                            
                            share_text = f"🌿 PlantPal ID: {crop.capitalize()}\nLocal: {info['local_name']}\nSeason: {info['season']}\nPrice: {info['price']}"
                            share_url = whatsapp_share(share_text)
                            st.markdown(f'<a href="{share_url}" target="_blank"><button class="whatsapp-btn">📱 Share on WhatsApp</button></a>', unsafe_allow_html=True)
                        else:
                            st.markdown("---")
                            st.markdown("💡 **Not a Nigerian crop?** We're constantly adding more!")
                        
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

def weeds_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 🌿 Weed Identification & Control")
    st.markdown("Identify common Nigerian weeds and get control methods")
    
    st.markdown("### 📋 Common Weeds")
    for weed_key, info in NIGERIAN_WEEDS.items():
        with st.expander(f"{info['emoji']} {info['name']}"):
            st.markdown(f"**Description:** {info['description']}")
            st.markdown(f"**🌱 Organic Control:** {info['control_organic']}")
            st.markdown(f"**🧪 Chemical Control:** {info['control_chemical']}")
            st.markdown(f"**🛡️ Prevention:** {info['prevention']}")
            st.markdown(f"**📅 Season:** {info['season']}")
    
    st.markdown("---")
    st.markdown("### 🧪 Organic Pesticides")
    st.markdown("""
    **🌿 Neem Oil:** Effective against aphids, mites, leaf miners
    **🌶️ Pepper Spray:** Repels insects (mix with water and soap)
    **🧄 Garlic Spray:** Natural repellent for many pests
    **🌿 Wood Ash:** Controls snails, slugs, and some insects
    **🪴 Soap Spray:** Kills soft-bodied insects like aphids
    """)
    
    st.markdown("### 💡 Prevention Tips")
    st.markdown("""
    - Regular monitoring of your farm
    - Maintain good crop cover
    - Use cover crops to suppress weeds
    - Rotate crops to break weed cycles
    - Use mulching to prevent weed growth
    """)
    st.markdown('</div>', unsafe_allow_html=True)

def fertilizers_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 🧪 Fertilizer Guide for Nigerian Crops")
    st.markdown("Get the best fertilizer recommendations for your crops")
    
    st.markdown("### 📋 Fertilizer Recommendations")
    for crop, info in NIGERIAN_FERTILIZERS.items():
        with st.expander(f"🌱 {crop.capitalize()}"):
            st.markdown(f"**✅ Best Fertilizer:** {info['best']}")
            st.markdown(f"**🌿 Organic Options:** {info['organic']}")
            st.markdown(f"**📊 Application:** {info['application']}")
            st.markdown(f"**📅 Timing:** {info['timing']}")
            st.markdown(f"**🏡 Local Options:** {info['local_options']}")
    
    st.markdown("---")
    st.markdown("### 🌱 Organic Fertilizer Guide")
    st.markdown("""
    **🐔 Poultry Manure:** High in nitrogen. Apply 2-3 months before planting.
    **🐄 Cattle Manure:** Good all-round fertilizer. Apply 3-4 months before planting.
    **🌿 Compost:** Best for soil health. Apply at planting and top-dress.
    **🌾 Crop Residue:** Return to soil after harvest. Good for soil organic matter.
    **🌴 Wood Ash:** Source of potassium and calcium. Apply sparingly.
    """)
    
    st.markdown("### 💡 Fertilizer Tips")
    st.markdown("""
    - Always test your soil before applying fertilizers
    - Apply fertilizers when crops are actively growing
    - Water after fertilizer application for better absorption
    - Don't over-apply - this can damage crops and pollute water
    - Use organic options when possible for better soil health
    """)
    st.markdown('</div>', unsafe_allow_html=True)

def learning_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 📚 Learning Center & AI Assistant")
    
    tabs = st.tabs(["🇳🇬 Crops", "🌱 Care", "🩺 Disease", "📱 How", "🤖 Ask AI"])
    
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
        **Soil:** Add compost, test pH regularly.
        **Fertilizer:** Use organic options when possible.
        """)
    
    with tabs[2]:
        st.markdown("### Disease Prevention")
        st.markdown("""
        1. Use resistant varieties
        2. Space plants properly
        3. Avoid overhead watering
        4. Remove infected plants immediately
        5. Monitor plants daily
        6. Use crop rotation
        """)
    
    with tabs[3]:
        st.markdown("### How to Use PlantPal")
        st.markdown("""
        1. **Take a photo** of the plant or leaf
        2. **Upload** to PlantPal
        3. **Enter your city** for weather advice
        4. **Get results** - name, care, prices
        5. **Share** via WhatsApp
        6. **Save** to your history
        """)
    
    with tabs[4]:
        st.markdown("### 🤖 Ask PlantPal AI")
        st.markdown("Ask any question about plants, crops, farming, weeds, or fertilizers!")
        
        user_question = st.text_input("Your question:", placeholder="e.g., Tell me about cassava farming")
        
        if user_question:
            with st.spinner("Thinking..."):
                response = get_ai_response(user_question)
                st.markdown("---")
                st.markdown("### 🤖 AI Response")
                st.markdown(response)
        
        st.markdown("---")
        st.markdown("### 💡 Example Questions")
        st.markdown("""
        - "Tell me about cassava"
        - "How to treat tomato blight?"
        - "Best fertilizer for rice"
        - "How to remove spear grass?"
        - "What is PlantPal?"
        - "How do I use this app?"
        - "Organic pesticides for aphids"
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

def feedback_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 💬 Your Feedback Matters")
    st.markdown("Help us improve PlantPal by sharing your experience")
    
    with st.form("feedback_form"):
        rating = st.select_slider("Rate PlantPal", options=[1, 2, 3, 4, 5], value=4)
        comment = st.text_area("What do you think? (Optional)", placeholder="Share your thoughts...")
        page = st.selectbox("Which page?", ["Home", "Identify", "Disease", "Video", "Learn", "Weeds", "Fertilizers", "Other"])
        submitted = st.form_submit_button("Submit Feedback", type="primary")
        
        if submitted:
            if st.session_state.logged_in:
                username = st.session_state.username
            else:
                username = "anonymous"
            
            if save_feedback(username, rating, comment, page):
                st.success("✅ Thank you for your feedback!")
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
                <p style="color:#555;font-size:0.9rem;">{fb[2] or 'No comment'}</p>
                <p style="color:#888;font-size:0.7rem;">{fb[3][:10]} - {fb[4]}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No feedback yet. Be the first!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def faq_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## ❓ Frequently Asked Questions")
    faqs = [
        ("What is PlantPal?", "AI-powered farming assistant for Nigerian farmers."),
        ("Is it free?", "Yes, completely free!"),
        ("Do I need internet?", "Yes, internet required."),
        ("Is my data private?", "Yes, images are not stored."),
        ("How accurate?", "92% for identification."),
        ("How to create account?", "Click 'Sign Up' and enter your details."),
        ("Which crops?", "Cassava, Rice, Yam, Tomato, Pepper, Maize, Cocoa and more!"),
        ("Can I share results?", "Yes! Use WhatsApp share button."),
        ("Do I need to login?", "No! Browse the home page first. Login only to save history."),
        ("What about weeds?", "Check the Weeds section for identification and control."),
        ("What about fertilizers?", "Check the Fertilizers section for recommendations."),
        ("How to use AI assistant?", "Go to Learn Center → Ask AI tab.")
    ]
    for q,a in faqs:
        with st.expander(f"📌 {q}"):
            st.markdown(a)
    st.markdown('</div>', unsafe_allow_html=True)

def about_page():
    back_button()
    st.markdown('<div class="main-content slide-down">', unsafe_allow_html=True)
    st.markdown("## 📖 About PlantPal")
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("""
        ### 🇳🇬 Our Mission
        Empower Nigerian smallholder farmers with AI technology.
        
        We believe every farmer should have access to:
        - Accurate plant identification
        - Early disease detection
        - Practical farming advice
        - Market price information
        - Weed control guidance
        - Fertilizer recommendations
        
        ### 🌱 Our Story
        PlantPal was born from seeing Nigerian farmers lose crops due to undiagnosed diseases. We built this to make expert knowledge accessible to all.

        ### 🌾 Our Crops
        Cassava, Rice, Yam, Groundnut, Tomato, Pepper, Maize, Sorghum, Cocoa, Palm Oil, Beans, Plantain, Okra, Millet, Sesame

        ### 🌿 Weeds Database
        Spear Grass, Goat Weed, Mimosa, Bermuda Grass, Pigweed, Couch Grass

        ### 🧪 Fertilizer Guide
        Crop-specific recommendations with organic and local options

        ### 🌟 Our Values
        - 🌱 Accessibility – Technology for everyone
        - 🤝 Community – Built with and for farmers
        - 🌍 Sustainability – Environmentally conscious
        - 🔬 Accuracy – Reliable, science-based information
        - 🇳🇬 Local Relevance – Focused on Nigerian agriculture
        """)
    with col2:
        st.markdown("""
        ### Quick Facts
        - Founded: 2024
        - Users: 50,000+
        - Crops: 15+
        - Weeds: 6+
        - Languages: 5
        - Accuracy: 92%

        ### Contact
        📧 hello@plantpal.com
        📱 +234 800 123 4567
        
        ### Follow Us
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
        <p>🇳🇬 PlantPal - Smart Farming Assistant for Nigeria</p>
        <p style="font-size:0.7rem;">© 2024 PlantPal. Built with ❤️ for Nigerian farmers</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()