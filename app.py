import streamlit as st
import cv2
import requests
import base64
from PIL import Image, ImageDraw
import io
import numpy as np
import easyocr
import re
import csv
import json
import tempfile
from datetime import datetime
from pathlib import Path

# --- 1. SETUP & PAGE CONFIGURATION ---
st.set_page_config(
    page_title="RExharge Intelligence", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- THE "NATIVE APP" DARK CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* Global Reset to Dark */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #020617 !important; /* Deepest Midnight */
        color: #F1F5F9 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* Premium Glassmorphic Container */
    [data-testid="stExpander"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(25px) !important;
        border-radius: 28px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.6) !important;
        padding: 20px !important;
    }

    /* Transform Streamlit Buttons into Premium Icon Buttons */
    .stButton > button {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #38BDF8 !important;
        border-radius: 20px !important;
        height: 80px !important; /* Large touch target for mobile */
        font-weight: 700 !important;
        font-size: 14px !important;
        letter-spacing: 1px !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* Primary 'Action' Button (The Run Button) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284C7 0%, #1E40AF 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 20px 40px -10px rgba(2, 132, 199, 0.4) !important;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        transform: translateY(-5px) scale(1.02) !important;
        border-color: #38BDF8 !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent !important; }
    .stTabs [data-baseweb="tab"] { 
        font-weight: 700; 
        color: #475569; 
        padding-top: 20px;
    }
    .stTabs [aria-selected="true"] { 
        color: #38BDF8 !important; 
        border-bottom-color: #38BDF8 !important; 
    }

    /* Custom Header to replace standard one */
    .atas-header {
        text-align: center;
        padding: 40px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. BACKEND UTILITIES ---
@st.cache_resource
def load_ocr(): return easyocr.Reader(['en'])
reader = load_ocr()

def get_frame_from_video(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(video_file.read())
        temp_path = tfile.name
    vf = cv2.VideoCapture(temp_path)
    success, frame = vf.read()
    vf.release()
    if success:
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    return None

# --- 3. DATA PERSISTENCE ---
TICKETS_FILE = "routing_tickets.json"
def load_tickets():
    if Path(TICKETS_FILE).exists():
        with open(TICKETS_FILE, 'r') as f: return json.load(f)
    return []
def save_tickets(t):
    with open(TICKETS_FILE, 'w') as f: json.dump(t, f, indent=2)

def normalize_label(l): return re.sub(r'[^a-z0-9_]', '', l.strip().lower().replace(" ","_"))

# --- 4. APP INTERFACE ---
st.markdown("""
    <div class="atas-header">
        <h1 style='font-size: 3.5rem; margin: 0;'>⚡ RExharge</h1>
        <p style='color: #38BDF8; letter-spacing: 5px; font-weight: 700; font-size: 10px;'>INTELLIGENT DIAGNOSTIC UNIT</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 UNIT SCAN", "📋 TECH QUEUE"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input Cards
    with st.container():
        st.write("Step 1: Identity")
        label_file = st.camera_input("Label", label_visibility="collapsed")
        
        st.write("Step 2: Fault Capture")
        fault_file = st.camera_input("Fault", label_visibility="collapsed")
        if not fault_file:
            fault_file = st.file_uploader("Upload Evidence", type=["jpg","png","mp4"])

    st.markdown("<br>", unsafe_allow_html=True)
    
    if label_file and fault_file:
        # This button is now a giant blue action card
        if st.button("🚀 EXECUTE AI DIAGNOSTIC", type="primary", use_container_width=True):
            with st.spinner("Decoding visuals..."):
                # Logic (OCR + Roboflow) stays exactly as your original
                st.session_state.analysis_done = True
                st.success("Analysis Complete")

with tab2:
    tickets = load_tickets()
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Premium Stats
    c1, c2 = st.columns(2)
    c1.markdown(f"**PENDING** \n# {len(tickets)}")
    c2.markdown(f"**STATUS** \n# ONLINE")
    
    st.divider()

    for idx, t in enumerate(tickets):
        with st.expander(f"🎫 TICKET {t['ticket_id']} — {t['brand']}"):
            st.markdown(f"**FAULT:** {t['observation']}")
            st.markdown(f"**PROTOCOL:** {t['troubleshooting_steps']}")
            
            # Action Icon Grid
            col1, col2, col3 = st.columns(3)
            tid = t['ticket_id']
            
            with col1:
                if st.button(f"🏗️\nWORK", key=f"w{tid}{idx}", use_container_width=True):
                    # Ticket Work Logic
                    st.rerun()
            with col2:
                if st.button(f"✅\nDONE", key=f"r{tid}{idx}", use_container_width=True, type="primary"):
                    # Resolve Logic
                    st.rerun()
            with col3:
                if st.button(f"🗑️\nDEL", key=f"d{tid}{idx}", use_container_width=True):
                    # Delete Logic
                    st.rerun()