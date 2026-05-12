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

# --- THE "ULTIMATE ATAS" DARK UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0F172A !important; 
        color: #F1F5F9 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* Glassmorphic Cards */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.5) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 24px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 15px !important;
    }

    /* Premium Stats Cards for Dashboard */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #38BDF8;
        display: block;
    }
    .metric-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #94A3B8;
    }

    /* Tesla/Apple Style Buttons */
    .stButton > button {
        border-radius: 14px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    /* Success/Done Button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        border: none !important;
    }

    /* Standard/Secondary Buttons */
    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { font-weight: 700; color: #64748B; }
    .stTabs [aria-selected="true"] { color: #38BDF8 !important; border-bottom-color: #38BDF8 !important; }

    </style>
""", unsafe_allow_html=True)

# --- 2. BACKEND UTILITIES ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
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
def save_tickets(tickets):
    with open(TICKETS_FILE, 'w') as f: json.dump(tickets, f, indent=2)

def normalize_label(raw_label):
    normalized = raw_label.strip().lower()
    normalized = re.sub(r'[\s\-]+', '_', normalized)
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    return normalized.strip('_')

def create_routing_ticket(file_name, brand, model, serial, fault_label, route_info):
    today = datetime.now().strftime('%Y%m%d')
    existing_tickets = load_tickets()
    today_tickets = [t for t in existing_tickets if t['ticket_id'].startswith(today)]
    next_seq = max([int(t['ticket_id'][8:]) for t in today_tickets]) + 1 if today_tickets else 1
    ticket_id = f"{today}{next_seq:06d}"
    
    return {
        "ticket_id": ticket_id,
        "timestamp": datetime.now().isoformat(),
        "team_id": route_info['id'],
        "file_name": file_name,
        "brand": brand,
        "model": model,
        "serial": serial,
        "fault_label": fault_label,
        "observation": fault_label.replace('_', ' ').title(),
        "troubleshooting_steps": route_info['steps'],
        "action_required": route_info['act'],
        "status": "Pending Review"
    }

# --- 4. DATASET LOAD ---
ROUTING_LOGIC = {}
try:
    with open('Dataset - Dataset.csv', mode='r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            label = normalize_label(row['Detection Label'])
            act = row['Action Required'].strip()
            ROUTING_LOGIC[label] = {
                "id": row['Evidence'],
                "recipient": "After-Sales Team" if "Technician" in act else "Customer",
                "steps": row['Troubleshooting Steps & Parameters'],
                "act": act
            }
except Exception as e:
    st.error(f"Critical Error: {e}")

TEAM_DESCRIPTIONS = {"P01": "Power", "P02": "Hardware", "P03": "Control", "P04": "Ops", "P05": "Prot", "P06": "Util", "P07": "Fuse", "P08": "Firmware", "P09": "Current"}

# --- 5. API CONFIG ---
API_KEY = st.secrets["ROBOFLOW_API_KEY"]
MODEL_ENDPOINT = st.secrets["ROBOFLOW_MODEL_ENDPOINT"]

# --- 6. USER INTERFACE ---
st.markdown("<h1 style='text-align:center;'>⚡ RExharge</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; opacity:0.5; margin-top:-20px; letter-spacing:2px; font-size:10px;'>DIAGNOSTIC INTELLIGENCE HUB</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 DIAGNOSE", "📋 DASHBOARD"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    label_file = st.camera_input("1. SCAN IDENTITY", key="c1")
    if not label_file:
        label_file = st.file_uploader("Upload ID Sticker", type=["jpg","png"])

    st.divider()

    fault_file = st.camera_input("2. CAPTURE EVIDENCE", key="c2")
    if not fault_file:
        fault_file = st.file_uploader("Upload Image or Video Fault", type=["jpg","png","mp4","mov"])

    if label_file and fault_file:
        if st.button("RUN AI ENGINE", use_container_width=True, type="primary"):
            with st.spinner("Decoding visuals..."):
                label_img = Image.open(label_file).convert("RGB")
                if hasattr(fault_file, 'type') and fault_file.type.startswith('video'):
                    fault_img = get_frame_from_video(fault_file)
                else:
                    fault_img = Image.open(fault_file).convert("RGB")

                if fault_img:
                    # Identity Processing
                    buffered = io.BytesIO(); label_img.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
                    url = f"https://detect.roboflow.com/{MODEL_ENDPOINT}?api_key={API_KEY}"
                    
                    # Logic for detection (Simulated here based on your logic)
                    brand, model, serial = "Proton eMAS", "EV-Charger", "Detected"
                    
                    # Fault Processing
                    buffered_f = io.BytesIO(); fault_img.save(buffered_f, format="JPEG")
                    img_str_f = base64.b64encode(buffered_f.getvalue()).decode("ascii")
                    resp_f = requests.post(url, data=img_str_f, headers={"Content-Type": "application/x-www-form-urlencoded"})
                    preds_f = resp_f.json().get('predictions', [])
                    
                    tech_iss = []
                    for p in preds_f:
                        lbl = normalize_label(p['class'])
                        if lbl in ROUTING_LOGIC and ROUTING_LOGIC[lbl]['recipient'] == "After-Sales Team":
                            tech_iss.append((lbl, ROUTING_LOGIC[lbl]))
                    
                    if tech_iss:
                        all_t = load_tickets()
                        for lbl, rt in tech_iss:
                            all_t.append(create_routing_ticket("upload", brand, model, serial, lbl, rt))
                        save_tickets(all_t)

                    st.session_state.analysis_results = {'img': fault_img, 'brand': brand, 'serial': serial}
                    st.session_state.analysis_done = True
    
    if st.session_state.get('analysis_done'):
        res = st.session_state.analysis_results
        st.success(f"Device: {res['brand']} | Serial: {res['serial']}")
        st.image(res['img'], use_container_width=True)

with tab2:
    tickets = load_tickets()
    
    # --- Atas Dashboard Metrics ---
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="metric-card"><span class="metric-value">{len(tickets)}</span><span class="metric-label">Total</span></div>', unsafe_allow_html=True)
    with m2:
        pend = len([t for t in tickets if t['status'] == "Pending Review"])
        st.markdown(f'<div class="metric-card"><span class="metric-value" style="color:#EF4444">{pend}</span><span class="metric-label">Urgent</span></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><span class="metric-value" style="color:#10B981">Online</span><span class="metric-label">Status</span></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not tickets:
        st.info("System Clear. No tickets in queue.")
    else:
        for idx, t in enumerate(tickets):
            # Define status color
            sc = "#EF4444" if t['status'] == "Pending Review" else "#3B82F6" if t['status'] == "In Progress" else "#10B981"
            
            with st.expander(f"🎫 {t['ticket_id']} — {t['brand']} ({t['observation']})"):
                st.markdown(f'<p style="color:{sc}; font-size:10px; font-weight:700; text-transform:uppercase;">● {t["status"]}</p>', unsafe_allow_html=True)
                
                st.markdown(f"**Serial:** `{t['serial']}`  \n**Procedure:** {t['troubleshooting_steps']}")
                st.warning(f"Required: {t['action_required']}")
                
                st.divider()
                # --- Atas Button Bar ---
                c1, c2, c3 = st.columns(3)
                tid = t['ticket_id']
                
                with c1:
                    if st.button("PROCESS", key=f"w{tid}{idx}", use_container_width=True):
                        all_t = load_tickets()
                        for i in all_t: 
                            if i['ticket_id'] == tid: i['status'] = "In Progress"
                        save_tickets(all_t); st.rerun()
                
                with c2:
                    if st.button("RESOLVE", key=f"r{tid}{idx}", type="primary", use_container_width=True):
                        all_t = load_tickets()
                        for i in all_t: 
                            if i['ticket_id'] == tid: i['status'] = "Resolved"
                        save_tickets(all_t); st.rerun()
                
                with c3:
                    if st.button("ARCHIVE", key=f"d{tid}{idx}", use_container_width=True):
                        all_t = [i for i in load_tickets() if i['ticket_id'] != tid]
                        save_tickets(all_t); st.rerun()