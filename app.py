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
    page_title="RExharge Smart Diagnostic Hub", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- DARK MODE "ATAS" PREMIUM UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: #E2E8F0 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background-color: #0F172A; 
    }

    h1 {
        color: #F8FAFC;
        font-weight: 700;
        letter-spacing: -1px;
        text-align: center;
        margin-top: -30px;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #38BDF8, #1D4ED8);
        color: white;
        border-radius: 50px;
        padding: 14px 24px;
        border: none;
        box-shadow: 0 10px 15px -3px rgba(56, 189, 248, 0.2);
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }

    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }

    [data-testid="stFileUploader"] section {
        border-radius: 16px;
        border: 2px dashed #334155;
        background-color: #1E293B;
    }

    .stMarkdown p, .stMarkdown div {
        color: #CBD5E1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE UTILITIES & OCR ---
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
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame)
    return None

# --- 3. SESSION STATE & DATA PERSISTENCE ---
if 'last_label_name' not in st.session_state:
    st.session_state.last_label_name = None
    st.session_state.last_fault_name = None
    st.session_state.analysis_done = False
    st.session_state.analysis_results = {}

TICKETS_FILE = "routing_tickets.json"

def load_tickets():
    if Path(TICKETS_FILE).exists():
        try:
            with open(TICKETS_FILE, 'r') as f:
                content = f.read()
                return json.loads(content) if content else []
        except Exception: return []
    return []

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

def normalize_label(raw_label):
    normalized = raw_label.strip().lower()
    normalized = re.sub(r'[\s\-]+', '_', normalized)
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    return normalized.strip('_')

def create_routing_ticket(file_name, brand, model, serial, fault_label, route_info):
    today = datetime.now().strftime('%Y%m%d')
    existing_tickets = load_tickets()
    today_tickets = [t for t in existing_tickets if t['ticket_id'].startswith(today)]
    
    if today_tickets:
        seq_nums = [int(t['ticket_id'][8:]) for t in today_tickets if t['ticket_id'][8:].isdigit()]
        next_seq = max(seq_nums) + 1 if seq_nums else 1
    else:
        next_seq = 1
        
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

# --- 4. DATASET & ROUTING LOGIC ---
ROUTING_LOGIC = {}
try:
    with open('Dataset - Dataset.csv', mode='r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            label = normalize_label(row['Detection Label'])
            action_text = row['Action Required'].strip()
            recipient = "After-Sales Team" if "Technician" in action_text else "Customer"
            ROUTING_LOGIC[label] = {
                "id": row['Evidence'],
                "recipient": recipient,
                "steps": row['Troubleshooting Steps & Parameters'],
                "act": action_text,
                "severity": row.get('Severity', 'Medium')
            }
except Exception as e:
    st.error(f"Critical Error: Could not load Dataset - Dataset.csv ({e})")

TEAM_DESCRIPTIONS = {
    "P01": "Power Supply Unit", "P02": "Core Hardware", "P03": "Control Circuitry",
    "P04": "Operational Switches", "P05": "Protection Systems", "P06": "Utility Connection",
    "P07": "Internal Fuse", "P08": "Grounding/Firmware", "P09": "Over Current Protection"
}

# --- 5. API CONFIGURATION ---
API_KEY = st.secrets["ROBOFLOW_API_KEY"]
MODEL_ENDPOINT = st.secrets["ROBOFLOW_MODEL_ENDPOINT"] 

# --- 6. USER INTERFACE TABS ---
tab1, tab2 = st.tabs(["🔍 Diagnostics", "📋 Tickets"])

with tab1:
    st.markdown("<h1>⚡ RExharge</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; margin-top:-15px;'>Smart Diagnostic Hub</p>", unsafe_allow_html=True)
    
    st.markdown("### 📸 1. Scan Charger Label")
    label_file = st.camera_input("Label Camera", key="label_cam", label_visibility="collapsed")
    if not label_file:
        label_file = st.file_uploader("Or upload image", type=["jpg", "jpeg", "png"], key="label_upload")

    st.divider()

    st.markdown("### 🎥 2. Capture Fault")
    fault_file = st.camera_input("Fault Camera", key="fault_cam", label_visibility="collapsed")
    if not fault_file:
        fault_file = st.file_uploader("Or upload image/video", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"], key="fault_upload")
    
    if label_file and fault_file:
        if st.button("🚀 Run Diagnostics", type="primary"):
            with st.spinner("AI Processing..."):
                # Processing Logic
                label_img = Image.open(label_file).convert("RGB")
                
                if hasattr(fault_file, 'type') and fault_file.type.startswith('video'):
                    fault_img = get_frame_from_video(fault_file)
                else:
                    fault_img = Image.open(fault_file).convert("RGB")

                if fault_img:
                    # Identity Logic
                    buffered = io.BytesIO()
                    label_img.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
                    url = f"https://detect.roboflow.com/{MODEL_ENDPOINT}?api_key={API_KEY}&confidence=25"
                    
                    resp = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"})
                    preds = resp.json().get('predictions', [])
                    
                    brand, model, serial = "Proton eMAS", "Unknown", "Not detected"
                    for p in preds:
                        x0, y0, x1, y1 = p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2
                        if p['class'] == "model_name":
                            roi = np.array(label_img.crop((x0, y0, x1, y1)))
                            res = reader.readtext(roi, detail=0)
                            if res: model = res[0]
                        elif p['class'] == "serial_number":
                            roi = np.array(label_img.crop((x0, y0, x1, y1)))
                            res = reader.readtext(roi, detail=0)
                            if res: serial = res[0]

                    # Fault Logic
                    buffered_f = io.BytesIO()
                    fault_img.save(buffered_f, format="JPEG")
                    img_str_f = base64.b64encode(buffered_f.getvalue()).decode("ascii")
                    resp_f = requests.post(url, data=img_str_f, headers={"Content-Type": "application/x-www-form-urlencoded"})
                    preds_f = resp_f.json().get('predictions', [])
                    
                    draw = ImageDraw.Draw(fault_img)
                    cust_iss, tech_iss = [], []
                    for p in preds_f:
                        lbl = normalize_label(p['class'])
                        if lbl in ROUTING_LOGIC:
                            draw.rectangle([p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2], outline="#38BDF8", width=8)
                            route = ROUTING_LOGIC[lbl]
                            if route['recipient'] == "Customer":
                                cust_iss.append((lbl, route))
                            else:
                                tech_iss.append((lbl, route))

                    if tech_iss:
                        current_tickets = load_tickets()
                        for lbl, rt in tech_iss:
                            current_tickets.append(create_routing_ticket(getattr(fault_file, 'name', 'upload'), brand, model, serial, lbl, rt))
                        save_tickets(current_tickets)

                    st.session_state.analysis_results = {
                        'brand': brand, 'model': model, 'serial': serial,
                        'customer_issues': cust_iss, 'technician_issues': tech_iss,
                        'annotated_fault_image': fault_img
                    }
                    st.session_state.analysis_done = True

    if st.session_state.analysis_done:
        res = st.session_state.analysis_results
        st.divider()
        st.info(f"**Device:** {res['brand']} / {res['model']}  | **SN:** `{res['serial']}`")
        st.image(res['annotated_fault_image'], use_container_width=True)
        
        if res['customer_issues']:
            st.markdown("### 👤 User Self-Fix")
            for lbl, rt in res['customer_issues']:
                with st.expander(f"⚠️ {lbl.replace('_',' ').title()}", expanded=True):
                    st.write(rt['steps'])
                    st.success(f"Action: {rt['act']}")

        if res['technician_issues']:
            st.markdown("### 🔧 Expert Repair Required")
            for lbl, rt in res['technician_issues']:
                with st.expander(f"🚨 {lbl.replace('_',' ').title()}"):
                    st.info(f"Team: {rt['id']} | Procedure: {rt['steps']}")

# --- 7. TAB 2: QUEUE MANAGEMENT DASHBOARD ---
with tab2:
    st.markdown("<h2 style='text-align: center; color: #F8FAFC;'>📋 Queue Management</h2>", unsafe_allow_html=True)
    tickets = load_tickets()
    
    if not tickets:
        st.info("📭 Inbox zero. No active tickets.")
    else:
        # Dashboard Overview
        m1, m2 = st.columns(2)
        m1.metric("Total Tickets", len(tickets))
        m2.metric("Critical Pending", len([t for t in tickets if t['status'] == "Pending Review"]))
        
        st.divider()
        
        # Filters
        f1, f2 = st.columns(2)
        with f1:
            team_filter = st.selectbox("Dept", ["All"] + sorted(list(set([t['team_id'] for t in tickets]))))
        with f2:
            status_filter = st.selectbox("Status", ["All", "Pending Review", "In Progress", "Resolved"])
        
        filtered = [t for t in tickets if (team_filter == "All" or t['team_id'] == team_filter) and (status_filter == "All" or t['status'] == status_filter)]
        
        for idx, ticket in enumerate(filtered):
            status_color = "#EF4444" if ticket['status'] == "Pending Review" else "#3B82F6" if ticket['status'] == "In Progress" else "#10B981"
            
            with st.expander(f"🎫 {ticket['ticket_id']} — {ticket['observation']}"):
                st.markdown(f'<span style="background-color: {status_color}; color: white; padding: 4px 12px; border-radius: 50px; font-size: 11px; font-weight: 700;">{ticket["status"]}</span>', unsafe_allow_html=True)
                
                st.markdown(f"**Hardware:** {ticket['brand']} / {ticket['model']}")
                st.markdown(f"**Serial:** `{ticket['serial']}`")
                
                with st.container(border=True):
                    st.markdown("**🛠️ Action Plan**")
                    st.caption(ticket['troubleshooting_steps'])
                    st.info(f"**Protocol:** {ticket['action_required']}")
                
                st.divider()
                
                # Action Buttons
                c1, c2, c3 = st.columns(3)
                tid = ticket['ticket_id']
                
                with c1:
                    if st.button("🏗️ Work", key=f"p_{tid}_{idx}", use_container_width=True):
                        all_t = load_tickets()
                        for item in all_t:
                            if item['ticket_id'] == tid: item['status'] = "In Progress"
                        save_tickets(all_t); st.rerun()
                
                with c2:
                    if st.button("✅ Done", key=f"r_{tid}_{idx}", use_container_width=True, type="primary"):
                        all_t = load_tickets()
                        for item in all_t:
                            if item['ticket_id'] == tid: item['status'] = "Resolved"
                        save_tickets(all_t); st.rerun()
                
                with c3:
                    if st.button("🗑️ Del", key=f"d_{tid}_{idx}", use_container_width=True):
                        all_t = [item for item in load_tickets() if item['ticket_id'] != tid]
                        save_tickets(all_t); st.rerun()