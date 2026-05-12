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

# --- THE "TESLA DASHBOARD" CSS NUKE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* 1. ABSOLUTE DARK MODE OVERRIDE */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: #000000 !important; /* Pure OLED Black */
        color: #F8FAFC !important;
    }

    #MainMenu, footer, header, [data-testid="stSidebar"] {
        display: none !important;
    }

    /* 2. EXTREME UPLOADER & CAMERA FIX */
    /* Target the container box */
    div[data-testid="stFileUploader"] > section {
        background-color: #0F172A !important; /* Deep Navy Background */
        border: 1px solid #0EA5E9 !important; /* Neon Blue Border */
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: inset 0 0 20px rgba(14, 165, 233, 0.1) !important;
    }
    
    /* Force ALL text inside the uploader to be readable */
    div[data-testid="stFileUploader"] *,
    [data-testid="stCameraInput"] > div > div > div * { 
        color: #E2E8F0 !important;
        font-weight: 600 !important;
    }
    
    /* --> THE FIX FOR CAMERA PERMISSION TEXT <-- */
    [data-testid="stCameraInput"] p, 
    [data-testid="stCameraInput"] div {
        color: #475569 !important; /* Slate grey to be visible against white backgrounds */
    }
    
    /* Force the Cloud icon to be blue */
    div[data-testid="stFileUploader"] svg {
        fill: #0EA5E9 !important; 
        color: #0EA5E9 !important;
    }

    /* Style the internal "Browse files" & "Take Photo" buttons */
    [data-testid="stFileUploader"] button,
    [data-testid="stCameraInput"] button {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #0EA5E9 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: bold !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFileUploader"] button:hover,
    [data-testid="stCameraInput"] button:hover {
        background-color: #0EA5E9 !important;
        color: #000000 !important;
    }

    /* Hide the "Drag and drop file here" subtext to keep it ultra clean */
    [data-testid="stFileUploadDropzone"] small {
        display: none !important;
    }

    /* 3. LUXURY CONTROL TILES (Replacing standard buttons) */
    .stButton > button {
        background: #0B1120 !important;
        border: 1px solid #1E293B !important;
        color: #38BDF8 !important;
        border-radius: 16px !important;
        height: 70px !important; /* Large touch target */
        font-weight: 800 !important;
        font-size: 14px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.8) !important;
        transition: all 0.2s ease-out !important;
        width: 100% !important;
    }
    .stButton > button:active, .stButton > button:hover {
        background: #0EA5E9 !important;
        color: #000000 !important;
        border: 1px solid #38BDF8 !important;
        transform: scale(0.98) !important; /* Satisfying press effect */
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.5) !important;
    }

    /* Primary "Action" Button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #0284C7, #1E40AF) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 0 30px rgba(2, 132, 199, 0.4) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(90deg, #38BDF8, #2563EB) !important;
        transform: scale(1.02) !important;
        color: #FFFFFF !important;
    }

    /* 4. DASHBOARD PANELS (Replacing Expanders) */
    [data-testid="stExpander"] {
        background: #09090B !important; 
        border: 1px solid #27272A !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.8) !important;
        margin-top: 15px !important;
    }
    [data-testid="stExpander"] details summary p {
        font-weight: 800 !important;
        color: #0EA5E9 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }

    /* 5. CUSTOM DASHBOARD TABS */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 2px solid #1E293B !important;
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748B !important; 
        font-weight: 800 !important; 
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        padding-bottom: 15px !important;
    }
    .stTabs [aria-selected="true"] { 
        color: #F8FAFC !important; 
        border-bottom: 3px solid #0EA5E9 !important; 
    }

    /* 6. Custom System Headers */
    .dash-header {
        font-size: 16px;
        font-weight: 800;
        color: #F8FAFC;
        margin-top: 25px;
        margin-bottom: 5px;
    }
    .dash-sub {
        font-size: 13px;
        color: #94A3B8;
        margin-bottom: 15px;
        font-weight: 400;
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
    pass # Silent fail to maintain Atas UI look

TEAM_DESCRIPTIONS = {
    "P01": "Power Supply Unit", "P02": "Core Hardware", "P03": "Control Circuitry",
    "P04": "Operational Switches", "P05": "Protection Systems", "P06": "Utility Connection",
    "P07": "Internal Fuse", "P08": "Grounding/Firmware", "P09": "Over Current Protection"
}

# --- 5. API CONFIGURATION ---
API_KEY = st.secrets["ROBOFLOW_API_KEY"]
MODEL_ENDPOINT = st.secrets["ROBOFLOW_MODEL_ENDPOINT"] 

# --- 6. MAIN SYSTEM INTERFACE ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="font-size: 3.5rem; margin-bottom: 0px; background: -webkit-linear-gradient(#FFFFFF, #94A3B8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⚡ RExharge</h1>
        <p style="color: #0EA5E9; letter-spacing: 5px; font-size: 10px; font-weight: 800; margin-top: -10px;">SYSTEM DIAGNOSTIC HUB</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["DIAGNOSTICS", "SYSTEM QUEUE"])

with tab1:
    # --- Input Section 1 ---
    st.markdown('<div class="dash-header">📸 1. Scan Charger Label</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Take a photo of the brand/model/serial sticker.</div>', unsafe_allow_html=True)
    
    label_camera = st.camera_input("Scanner", key="label_cam", label_visibility="collapsed")
    label_upload = st.file_uploader("Upload Asset", type=["jpg", "jpeg", "png"], key="label_upload", label_visibility="collapsed")
    label_file = label_camera if label_camera else label_upload

    # --- Input Section 2 ---
    st.markdown('<div class="dash-header">📸 2. Capture Fault (Image or Video)</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Record video or take a photo of the physical issue.</div>', unsafe_allow_html=True)
    
    fault_camera = st.camera_input("Capture", key="fault_cam", label_visibility="collapsed")
    fault_upload = st.file_uploader("Upload Media", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"], key="fault_upload", label_visibility="collapsed")
    fault_file = fault_camera if fault_camera else fault_upload
    
    if label_file and fault_file:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INITIATE DIAGNOSTIC PROTOCOL", type="primary"):
            with st.spinner("Processing Telemetry..."):
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
                    
                    try:
                        resp = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"})
                        preds = resp.json().get('predictions', [])
                    except:
                        preds = []
                    
                    brand, model, serial = "Proton eMAS", "Unknown", "Not detected"
                    for p in preds:
                        x0, y0, x1, y1 = p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2
                        if p['class'] == "model_name":
                            roi = np.array(label_image.crop((x0, y0, x1, y1)))
                            res = reader.readtext(roi, detail=0)
                            if res: model = res[0]
                        elif p['class'] == "serial_number":
                            roi = np.array(label_image.crop((x0, y0, x1, y1)))
                            res = reader.readtext(roi, detail=0)
                            if res: serial = res[0]

                    # Fault Logic
                    buffered_f = io.BytesIO()
                    fault_img.save(buffered_f, format="JPEG")
                    img_str_f = base64.b64encode(buffered_f.getvalue()).decode("ascii")
                    try:
                        resp_f = requests.post(url, data=img_str_f, headers={"Content-Type": "application/x-www-form-urlencoded"})
                        preds_f = resp_f.json().get('predictions', [])
                    except:
                        preds_f = []
                    
                    draw = ImageDraw.Draw(fault_img)
                    cust_iss, tech_iss = [], []
                    for p in preds_f:
                        lbl = normalize_label(p['class'])
                        if lbl in ROUTING_LOGIC:
                            draw.rectangle([p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2], outline="#0EA5E9", width=8)
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
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="dash-header">DIAGNOSTIC REPORT</div>', unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown(f"<span style='color:#0EA5E9; font-weight:800; font-size:12px;'>DEVICE TELEMETRY</span><br><b>{res['brand']} / {res['model']}</b><br><span style='color:#94A3B8; font-size:12px;'>SN: {res['serial']}</span>", unsafe_allow_html=True)
            
        st.image(res['annotated_fault_image'], use_container_width=True)
        
        if res['customer_issues']:
            for lbl, rt in res['customer_issues']:
                with st.expander(f"⚠️ REQUIRED USER ACTION", expanded=True):
                    st.markdown(f"**ISSUE:** {lbl.replace('_',' ').title()}")
                    st.write(rt['steps'])
                    st.success(f"RESOLUTION: {rt['act']}")

        if res['technician_issues']:
            for lbl, rt in res['technician_issues']:
                with st.expander(f"🚨 ESCALATED PROTOCOL"):
                    st.error(f"**FAULT DETECTED:** {lbl.replace('_',' ').title()}")
                    st.info(f"**ROUTED TO TEAM {rt['id']}** | Procedure: {rt['steps']}")

# --- 7. TAB 2: QUEUE MANAGEMENT DASHBOARD ---
with tab2:
    tickets = load_tickets()
    
    if not tickets:
        st.markdown("<br><br><p style='text-align:center; color:#94A3B8; font-weight:800;'>SYSTEM OPTIMAL. NO ACTIVE TICKETS.</p>", unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background: #09090B; border: 1px solid #1E293B; border-radius: 16px; padding: 20px; display: flex; justify-content: space-around; text-align: center; margin-bottom: 20px;">
                <div>
                    <span style="font-size: 24px; font-weight: 800; color: #F8FAFC;">{total}</span><br>
                    <span style="font-size: 10px; color: #64748B; letter-spacing: 2px;">TOTAL TICKETS</span>
                </div>
                <div>
                    <span style="font-size: 24px; font-weight: 800; color: #EF4444;">{crit}</span><br>
                    <span style="font-size: 10px; color: #64748B; letter-spacing: 2px;">CRITICAL</span>
                </div>
            </div>
        """.format(total=len(tickets), crit=len([t for t in tickets if t['status'] == "Pending Review"])), unsafe_allow_html=True)
        
        filtered = tickets
        
        st.markdown('<div class="dash-header">ACTIVE WORK ORDERS</div>', unsafe_allow_html=True)
        
        for idx, ticket in enumerate(filtered):
            status_color = "#EF4444" if ticket['status'] == "Pending Review" else "#0EA5E9" if ticket['status'] == "In Progress" else "#10B981"
            
            with st.expander(f"🎫 TICKET {ticket['ticket_id']} — {ticket['observation']}"):
                st.markdown(f'<span style="background-color: {status_color}; color: #000000; padding: 4px 12px; border-radius: 4px; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform:uppercase;">{ticket["status"]}</span>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"**UNIT:** {ticket['brand']} / {ticket['model']}<br>**SERIAL:** `{ticket['serial']}`", unsafe_allow_html=True)
                
                st.markdown("<br><p style='font-size:10px; color:#0EA5E9; font-weight:800; letter-spacing:1px; margin-bottom: 0px;'>TECHNICAL PROTOCOL</p>", unsafe_allow_html=True)
                st.write(ticket['troubleshooting_steps'])
                st.info(f"REQUIRED: {ticket['action_required']}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                tid = ticket['ticket_id']
                
                with c1:
                    if st.button("PROCESS", key=f"p_{tid}_{idx}", use_container_width=True):
                        all_t = load_tickets()
                        for item in all_t:
                            if item['ticket_id'] == tid: item['status'] = "In Progress"
                        save_tickets(all_t); st.rerun()
                
                with c2:
                    if st.button("RESOLVE", key=f"r_{tid}_{idx}", use_container_width=True):
                        all_t = load_tickets()
                        for item in all_t:
                            if item['ticket_id'] == tid: item['status'] = "Resolved"
                        save_tickets(all_t); st.rerun()
                
                with c3:
                    if st.button("ARCHIVE", key=f"d_{tid}_{idx}", use_container_width=True):
                        all_t = [item for item in load_tickets() if item['ticket_id'] != tid]
                        save_tickets(all_t); st.rerun()