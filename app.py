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

# --- THE ULTIMATE ATAS CSS NUKE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* 1. GLOBAL RESET */
    html, body, .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: #000000 !important; 
    }

    #MainMenu, footer, header, [data-testid="stSidebar"] {
        display: none !important;
    }

    /* 2. BASE BOX STYLING (NAVY PANELS) */
    div[data-testid="stFileUploader"] > section,
    [data-testid="stCameraInput"] > div {
        background-color: #0F172A !important; 
        border: 1px solid #0EA5E9 !important; 
        border-radius: 16px !important;
        padding: 24px !important;
    }

    /* -----------------------------------------------------------
       UPLOAD AREA: DISABLE RECTANGLE CLICK & STYLE BUTTON
       ----------------------------------------------------------- */

    /* Make the entire rectangle NOT clickable */
    [data-testid="stFileUploadDropzone"] {
        pointer-events: none !important;
        cursor: default !important;
    }

    /* Re-enable clicking ONLY for the actual button */
    [data-testid="stFileUploadDropzone"] button {
        pointer-events: auto !important;
        cursor: pointer !important;
        background-color: #1E293B !important;
        border: 1px solid #0EA5E9 !important;
        border-radius: 8px !important;
    }

    /* Force the "Browse files" text and Cloud Icon to Light Blue */
    [data-testid="stFileUploadDropzone"] button *, 
    [data-testid="stFileUploadDropzone"] svg,
    [data-testid="stFileUploadDropzone"] path {
        color: #38BDF8 !important;
        fill: #38BDF8 !important;
        -webkit-text-fill-color: #38BDF8 !important;
        font-weight: 700 !important;
    }

    /* -----------------------------------------------------------
       FIX TEXT VISIBILITY (LIGHT VS DARK)
       ----------------------------------------------------------- */

    /* A. UPLOADER INFO TEXT (200MB etc.) -> Bright White */
    div[data-testid="stFileUploader"] small,
    div[data-testid="stFileUploadDropzone"] small {
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 500 !important;
        opacity: 1 !important;
    }

    /* B. CAMERA PERMISSION TEXT -> Dark Grey for white prompt visibility */
    [data-testid="stCameraInput"] p, 
    [data-testid="stCameraInput"] span,
    [data-testid="stCameraInput"] label {
        color: #475569 !important; 
        -webkit-text-fill-color: #475569 !important;
        font-weight: 700 !important;
    }

    /* C. TAKE PHOTO BUTTON TEXT -> Light Blue */
    [data-testid="stCameraInput"] button * {
        color: #38BDF8 !important;
        -webkit-text-fill-color: #38BDF8 !important;
    }

    /* D. TABS -> High Contrast */
    .stTabs [data-baseweb="tab"] p {
        color: #94A3B8 !important; 
        font-weight: 700 !important;
    }
    .stTabs [aria-selected="true"] p {
        color: #F8FAFC !important; 
        font-weight: 800 !important;
    }

    /* E. UPLOADED FILE NAME -> Black text (Because the card is white) */
    [data-testid="stFileUploader"] [data-testid="stText"] span,
    [data-testid="stFileUploader"] .uploadedFileName {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* 3. MAIN INTERFACE ELEMENTS */
    .stButton > button {
        background: #0B1120 !important;
        border: 1px solid #1E293B !important;
        color: #38BDF8 !important;
        border-radius: 16px !important;
        height: 70px !important; 
        font-weight: 800 !important;
        text-transform: uppercase !important;
        width: 100% !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #0284C7, #1E40AF) !important;
        color: #FFFFFF !important;
    }

    /* Inner cards (Device Info / Action Plan) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(14, 165, 233, 0.3) !important;
        border-radius: 12px !important;
    }

    .dash-header { font-size: 18px; font-weight: 800; color: #F8FAFC; margin-top: 25px; }
    .dash-sub { font-size: 13px; color: #94A3B8; margin-bottom: 15px; }
    .data-label { color: #0EA5E9; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }
    .data-value { color: #F8FAFC; font-size: 14px; margin-bottom: 15px; }
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

# --- 3. SESSION STATE ---
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
                return json.load(f)
        except: return []
    return []

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

def normalize_label(raw_label):
    return re.sub(r'[^a-z0-9_]', '', raw_label.strip().lower().replace(' ', '_')).strip('_')

def create_routing_ticket(file_name, brand, model, serial, fault_label, route_info):
    today = datetime.now().strftime('%Y%m%d')
    existing = load_tickets()
    today_count = len([t for t in existing if t['ticket_id'].startswith(today)])
    ticket_id = f"{today}{today_count + 1:06d}"
    
    return {
        "ticket_id": ticket_id,
        "timestamp": datetime.now().isoformat(),
        "team_id": route_info['id'],
        "file_name": file_name,
        "brand": brand,
        "model": model,
        "serial": serial,
        "observation": fault_label.replace('_', ' ').title(),
        "troubleshooting_steps": route_info['steps'],
        "action_required": route_info['act'],
        "status": "Pending Review",
        "severity": route_info.get('severity', 'High') 
    }

# --- 4. DATASET LOGIC ---
ROUTING_LOGIC = {}
try:
    with open('Dataset - Dataset.csv', mode='r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            label = normalize_label(row['Detection Label'])
            ROUTING_LOGIC[label] = {
                "id": row['Evidence'],
                "steps": row['Troubleshooting Steps & Parameters'],
                "act": row['Action Required'],
                "recipient": "After-Sales Team" if "Technician" in row['Action Required'] else "Customer",
                "severity": row.get('Severity', 'Medium')
            }
except: pass 

TEAM_DESCRIPTIONS = {"P01": "Power Unit", "P02": "Hardware", "P03": "Control", "P04": "Switch", "P05": "Protection", "P06": "Utility", "P07": "Fuse", "P08": "Grounding", "P09": "Over Current"}

# --- 5. API CONFIG ---
API_KEY = st.secrets["ROBOFLOW_API_KEY"]
MODEL_ENDPOINT = st.secrets["ROBOFLOW_MODEL_ENDPOINT"] 

# --- 6. UI LAYOUT ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="font-size: 3.5rem; margin-bottom: 0px; background: -webkit-linear-gradient(45deg, #0EA5E9, #FFFFFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 0px 10px rgba(14, 165, 233, 0.3);">⚡ RExharge</h1>
        <p style="color: #38BDF8; letter-spacing: 5px; font-size: 10px; font-weight: 800; margin-top: -10px;">SYSTEM DIAGNOSTIC HUB</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["DIAGNOSTICS", "SYSTEM QUEUE"])

with tab1:
    st.markdown('<div class="dash-header">📸 1. Scan Charger Label</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Take a photo of the brand/model/serial sticker.</div>', unsafe_allow_html=True)
    l_cam = st.camera_input("Scanner", key="l_cam", label_visibility="collapsed")
    l_up = st.file_uploader("Up1", type=["jpg","png"], key="l_up", label_visibility="collapsed")
    l_file = l_cam if l_cam else l_up

    st.markdown('<div class="dash-header">📸 2. Capture Fault (Image or Video)</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Record video or take a photo of the physical issue.</div>', unsafe_allow_html=True)
    f_cam = st.camera_input("Capture", key="f_cam", label_visibility="collapsed")
    f_up = st.file_uploader("Up2", type=["jpg","png","mp4"], key="f_up", label_visibility="collapsed")
    f_file = f_cam if f_cam else f_up
    
    if l_file and f_file:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("START DIAGNOSTIC", type="primary"):
            with st.spinner("Processing..."):
                label_img = Image.open(l_file).convert("RGB")
                if hasattr(f_file, 'type') and f_file.type.startswith('video'):
                    fault_img = get_frame_from_video(f_file)
                else:
                    fault_img = Image.open(f_file).convert("RGB")

                if fault_img:
                    # Roboflow Logic 
                    buffered = io.BytesIO()
                    label_img.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
                    url = f"https://detect.roboflow.com/{MODEL_ENDPOINT}?api_key={API_KEY}&confidence=25"
                    
                    try:
                        resp = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"})
                        preds = resp.json().get('predictions', [])
                    except: preds = []
                    
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

                    # Fault Detect
                    buffered_f = io.BytesIO()
                    fault_img.save(buffered_f, format="JPEG")
                    img_str_f = base64.b64encode(buffered_f.getvalue()).decode("ascii")
                    try:
                        resp_f = requests.post(url, data=img_str_f, headers={"Content-Type": "application/x-www-form-urlencoded"})
                        preds_f = resp_f.json().get('predictions', [])
                    except: preds_f = []
                    
                    draw = ImageDraw.Draw(fault_img)
                    cust_iss, tech_iss = [], []
                    for p in preds_f:
                        lbl = normalize_label(p['class'])
                        if lbl in ROUTING_LOGIC:
                            x0, y0, x1, y1 = p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2
                            draw.rectangle([x0, y0, x1, y1], outline="#EF4444", width=6) 
                            route = ROUTING_LOGIC[lbl]
                            if route['recipient'] == "Customer": cust_iss.append((lbl, route))
                            else: tech_iss.append((lbl, route))

                    routed_tickets = []
                    if tech_iss:
                        current_t = load_tickets()
                        for lbl, rt in tech_iss:
                            new_t = create_routing_ticket(getattr(f_file, 'name', 'upload'), brand, model, serial, lbl, rt)
                            current_t.append(new_t); routed_tickets.append(new_t)
                        save_tickets(current_t)

                    st.session_state.analysis_results = {
                        'brand': brand, 'model': model, 'serial': serial,
                        'customer_issues': cust_iss, 'technician_issues': tech_iss,
                        'annotated_fault_image': fault_img, 'routed_tickets': routed_tickets
                    }
                    st.session_state.analysis_done = True

    if st.session_state.analysis_done:
        res = st.session_state.analysis_results
        st.markdown('<div class="dash-header">DIAGNOSTIC REPORT</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<span style='color:#0EA5E9; font-weight:800; font-size:12px;'>DEVICE TELEMETRY</span><br><b>{res['brand']} / {res['model']}</b><br><span style='color:#94A3B8; font-size:12px;'>SN: {res['serial']}</span>", unsafe_allow_html=True)
        st.image(res['annotated_fault_image'], use_container_width=True)
        
        for lbl, rt in res['customer_issues']:
            with st.expander(f"⚠️ REQUIRED USER ACTION", expanded=True):
                st.markdown('<p class="data-label">OBSERVATION</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{lbl.replace("_"," ").title()}</p>', unsafe_allow_html=True)
                st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{rt["steps"]}</p>', unsafe_allow_html=True)
                st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value" style="color:#10B981;">{rt["act"]}</p>', unsafe_allow_html=True)

        for i, (lbl, rt) in enumerate(res['technician_issues']):
            t_id = res['routed_tickets'][i]['ticket_id']
            with st.expander(f"🚨 ESCALATED PROTOCOL"):
                st.markdown(f'<p class="data-label">TICKET ID: {t_id}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{lbl.replace("_"," ").title()} (Severity: {rt["severity"]})</p>', unsafe_allow_html=True)
                st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{rt["steps"]}</p>', unsafe_allow_html=True)
                st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value" style="color:#EF4444;">{rt["act"]}</p>', unsafe_allow_html=True)

with tab2:
    tickets = load_tickets()
    if not tickets:
        st.markdown("<p style='text-align:center; color:#94A3B8; font-weight:800; margin-top:50px;'>SYSTEM OPTIMAL. NO ACTIVE TICKETS.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="background: #09090B; border: 1px solid #1E293B; border-radius: 16px; padding: 20px; display: flex; justify-content: space-around; text-align: center; margin-bottom: 20px;">
                <div><span style="font-size: 24px; font-weight: 800; color: #F8FAFC;">{len(tickets)}</span><br><span style="font-size: 10px; color: #64748B; letter-spacing: 2px;">TOTAL</span></div>
                <div><span style="font-size: 24px; font-weight: 800; color: #EF4444;">{len([t for t in tickets if t['status'] == "Pending Review"])}</span><br><span style="font-size: 10px; color: #64748B; letter-spacing: 2px;">CRITICAL</span></div>
            </div>""", unsafe_allow_html=True)
        for idx, ticket in enumerate(tickets):
            with st.expander(f"🎫 {ticket['ticket_id']} — {ticket['observation']}"):
                st.markdown(f"**UNIT:** {ticket['brand']} / {ticket['model']} (SN: {ticket['serial']})")
                st.info(f"**PROTOCOL:** {ticket['troubleshooting_steps']}")
                st.error(f"**ACTION:** {ticket['action_required']}")
                c1, c2, c3 = st.columns(3)
                if c1.button("PROCESS", key=f"p_{idx}"):
                    ticket['status'] = "In Progress"; save_tickets(tickets); st.rerun()
                if c2.button("RESOLVE", key=f"r_{idx}"):
                    ticket['status'] = "Resolved"; save_tickets(tickets); st.rerun()
                if c3.button("ARCHIVE", key=f"d_{idx}"):
                    tickets.pop(idx); save_tickets(tickets); st.rerun()