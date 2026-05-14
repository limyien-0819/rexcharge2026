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
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

# --- 1. SETUP & PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Watt's Up Smart Diagnostic Hub", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ==============================
   TITLE GRADIENT FIX
============================== */
h1.gradient-title {
    background: -webkit-linear-gradient(45deg, #0284C7, #7DD3FC, #E0F2FE) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    text-shadow: 0px 0px 20px rgba(56, 189, 248, 0.4) !important;
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    margin-bottom: 0px !important;
}

/* ==============================
   DASHBOARD INSTRUCTIONS (WHITE ONLY)
============================== */
.stMarkdown:not(:has(h1.gradient-title)):not(:has(.stButton)),
.stMarkdown:not(:has(h1.gradient-title)):not(:has(.stButton)) * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

[data-testid="stMarkdownContainer"]:not(:has(h1.gradient-title)):not(:has(.stButton)),
[data-testid="stMarkdownContainer"]:not(:has(h1.gradient-title)):not(:has(.stButton)) * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* ==============================
   GLOBAL RESET
============================== */
html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: #000000 !important;
}

#MainMenu, footer, header, [data-testid="stSidebar"] {
    display: none !important;
}

/* ==============================
   BASE BOXES
============================== */
div[data-testid="stFileUploader"] > section,
[data-testid="stCameraInput"] > div {
    background-color: #0F172A !important;
    border: 1px solid #0EA5E9 !important;
    border-radius: 16px !important;
    padding: 24px !important;
}

/* ==============================
   UPLOAD & CAMERA BUTTONS
============================== */
[data-testid="stCameraInput"] button,
[data-testid="stCameraInput"] button *,
[data-testid="stFileUploadDropzone"] button,
[data-testid="stFileUploadDropzone"] button *,
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] label * {
    color: #38BDF8 !important;
    -webkit-text-fill-color: #38BDF8 !important;
    font-weight: 700 !important;
}

div[data-testid="stFileUploadDropzone"] > section > svg,
div[data-testid="stFileUploadDropzone"] > section > svg * {
    fill: #38BDF8 !important;
    stroke: #38BDF8 !important;
    color: #38BDF8 !important;
}

[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 400 !important;
}

/* ==============================
   UPLOADED FILE CARD FRAME
============================== */
[data-testid="stUploadedFile"] {
    background-color: #FFFFFF !important;
    border: 2px solid #E2E8F0 !important; 
    border-radius: 8px !important;
    padding: 10px !important;
    margin-top: 10px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
}

[data-testid="stUploadedFile"] span,
[data-testid="stUploadedFile"] .uploadedFileName,
[data-testid="stUploadedFile"] div {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-weight: 700 !important;
}

[data-testid="stUploadedFile"] button svg,
[data-testid="stUploadedFile"] button svg * {
    fill: #475569 !important;
    stroke: #475569 !important;
    color: #475569 !important;
}

[data-testid="stUploadedFile"] img {
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
}

/* ==============================
   IMAGE PREVIEW FRAME
============================== */
img {
    border: 3px solid #0EA5E9 !important;
    border-radius: 12px !important;
    padding: 6px !important; 
    background-color: #0F172A !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.8) !important;
    box-sizing: border-box !important; 
}

[data-testid="stImage"] img {
    border: 3px solid #0EA5E9 !important;
    border-radius: 12px !important;
    padding: 6px !important;
    background-color: #0F172A !important;
}

[data-testid="stFileUploadDropzone"] {
    pointer-events: none !important;
}
[data-testid="stFileUploadDropzone"] button {
    pointer-events: auto !important;
}

/* ==============================
   MULTISELECT FILTER TAGS
============================== */
span[data-baseweb="tag"] {
    background-color: #334155 !important; 
    color: #F8FAFC !important; 
}
span[data-baseweb="tag"] svg {
    fill: #94A3B8 !important;
}

/* ==============================
   "ATAS" EXPANDER STYLING
============================== */
[data-testid="stExpander"] details summary {
    background: linear-gradient(90deg, #0F172A, #1E293B) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 12px !important;
    padding: 15px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stExpander"] details summary:hover {
    border-color: rgba(56, 189, 248, 0.8) !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.15) !important;
}

[data-testid="stExpander"] details summary p {
    font-size: 15px !important;
    font-weight: 800 !important;
    color: #F8FAFC !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

[data-testid="stExpander"] details [data-testid="stExpanderDetails"] {
    background-color: #09090B !important; 
    border: 1px solid #1E293B !important;
    border-top: none !important;
    border-bottom-left-radius: 12px !important;
    border-bottom-right-radius: 12px !important;
    padding: 24px !important;
}

[data-testid="stExpander"] hr {
    display: none !important;
}

/* --- ATAS TEXT FORMATTING INSIDE EXPANDER --- */
.data-label {
    font-size: 10px !important;
    color: #64748B !important; 
    letter-spacing: 2px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    margin-bottom: 2px !important;
    margin-top: 12px !important;
}

.data-value {
    font-size: 15px !important;
    color: #F8FAFC !important; 
    font-weight: 500 !important;
    margin-bottom: 16px !important;
    line-height: 1.5 !important;
}

/* ==============================
   MAIN BUTTONS & CARDS
============================== */
.stButton > button {
    background: #0B1120 !important;
    border: 1px solid #1E293B !important;
    color: #38BDF8 !important;
    border-radius: 16px !important;
    height: 70px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    width: 100% !important;
    transition: all 0.2s ease !important; 
}

.stButton > button:hover {
    background: #1E293B !important;
    border-color: #38BDF8 !important;
}

.stButton > button:active {
    background: #38BDF8 !important; 
    color: #000000 !important; 
    transform: scale(0.98) !important; 
    box-shadow: inset 0 3px 5px rgba(0,0,0,0.5) !important; 
}

.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #0284C7, #1E40AF) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important; 
    border: none !important;
    border-radius: 20px !important; 
    box-shadow: 0 10px 25px rgba(2, 132, 199, 0.4) !important; 
    height: 75px !important; 
    letter-spacing: 2px !important; 
    transition: all 0.3s ease !important;
}

.stButton > button[kind="primary"] p {
    font-size: 16px !important; 
    font-weight: 900 !important; 
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 15px 35px rgba(2, 132, 199, 0.6) !important; 
    transform: translateY(-2px) !important; 
}

.stButton > button[kind="primary"]:active {
    transform: scale(0.98) !important; 
    box-shadow: inset 0 3px 5px rgba(0,0,0,0.5) !important; 
}

/* --- MANUAL ESCALATION BUTTON STYLING --- */
button[kind="secondary"] {
    background: #1E293B !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    border: 1px solid #475569 !important;
    height: 50px !important;
    margin-top: 10px !important;
}
button[kind="secondary"]:hover {
    border-color: #F59E0B !important;
    color: #F59E0B !important;
    -webkit-text-fill-color: #F59E0B !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(14, 165, 233, 0.3) !important;
    border-radius: 12px !important;
}

/* ==============================
   SECTION HEADERS (BOLD & LARGER)
============================== */
.dash-header {
    font-size: 22px !important; 
    font-weight: 900 !important; 
    color: #F8FAFC !important;
    margin-top: 30px !important;
    margin-bottom: 5px !important;
    letter-spacing: -0.5px;
}

.dash-sub {
    font-size: 14px !important;
    color: #94A3B8 !important;
    margin-bottom: 20px !important;
}

/* ==============================
   TABS STYLING
============================== */
.stTabs [data-baseweb="tab"] p {
    color: #94A3B8 !important;
    font-weight: 500 !important;
}

.stTabs [aria-selected="true"] p {
    color: #F8FAFC !important;
    font-weight: 900 !important;
}

/* --- STATUS TIMELINE STYLING --- */
.timeline-box {
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 1px;
}
.timeline-active {
    background-color: rgba(14, 165, 233, 0.2);
    border: 2px solid #0EA5E9;
    color: #0EA5E9;
}
.timeline-inactive {
    background-color: #09090B;
    border: 1px solid #1E293B;
    color: #475569;
}
.timeline-resolved {
    background-color: rgba(16, 185, 129, 0.2);
    border: 2px solid #10B981;
    color: #10B981;
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

def image_to_base64(img):
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=60)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def base64_to_image(b64_string):
    img_data = base64.b64decode(b64_string)
    img = Image.open(io.BytesIO(img_data))
    return img

# --- 3. SESSION STATE ---
if 'last_label_name' not in st.session_state:
    st.session_state.last_label_name = None
    st.session_state.last_fault_names = []
    st.session_state.analysis_done = False
    st.session_state.analysis_results = {}
if 'force_escalated' not in st.session_state:
    st.session_state.force_escalated = False

TICKETS_FILE = "routing_tickets.json"

def load_tickets():
    if Path(TICKETS_FILE).exists():
        try:
            with open(TICKETS_FILE, 'r') as f:
                content = f.read()
                return json.loads(content) if content else []
        except: return []
    return []

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

def normalize_label(raw_label):
    normalized = raw_label.strip().lower()
    normalized = re.sub(r'[\s\-]+', '_', normalized)
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    return normalized.strip('_')

def create_routing_ticket(file_name, brand, model, serial, fault_label, route_info, image_base64=None):
    my_timezone = timezone(timedelta(hours=8))
    current_time = datetime.now(my_timezone)
    
    today = current_time.strftime('%Y%m%d')
    existing_tickets = load_tickets()
    today_tickets = [t for t in existing_tickets if t['ticket_id'].startswith(today)]
    next_seq = (max([int(t['ticket_id'][8:]) for t in today_tickets if t['ticket_id'][8:].isdigit()] or [0]) + 1)
    ticket_id = f"{today}{next_seq:06d}"
    
    return {
        "ticket_id": ticket_id,
        "timestamp": current_time.isoformat(), 
        "team_id": route_info['id'],
        "file_name": file_name,
        "brand": brand,
        "model": model,
        "serial": serial,
        "observation": fault_label.replace('_', ' ').title(),
        "troubleshooting_steps": route_info['steps'],
        "action_required": route_info['act'],
        "status": "Pending Review",
        "severity": route_info.get('severity', 'High'),
        "image_data": image_base64 
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
                "recipient": "After-Sales Team" if "Technician" in row['Action Required'] else "Customer",
                "steps": row['Troubleshooting Steps & Parameters'],
                "act": row['Action Required'],
                "severity": row.get('Severity', 'Medium')
            }
except: pass 

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
        <h1 class="gradient-title">⚡ WATT'S UP</h1>
        <p style="color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; letter-spacing: 5px; font-size: 10px; font-weight: 800; margin-top: -10px;">SYSTEM DIAGNOSTIC HUB</p>
    </div>
""", unsafe_allow_html=True)

# --- FIX: Added "CHECK STATUS" Tab for Users ---
tab1, tab2, tab3, tab4 = st.tabs(["DIAGNOSTICS", "CHECK STATUS", "SERVICE TICKETS", "TICKET HISTORY"])

with tab1:
    st.markdown('<div class="dash-header">📸 1. Scan Charger Label</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Take a photo of the brand/model/serial sticker.</div>', unsafe_allow_html=True)
    
    l_cam = st.camera_input("Scanner", key="l_cam", label_visibility="collapsed")
    l_up = st.file_uploader("Upload Label", type=["jpg", "jpeg", "png"], key="l_up", label_visibility="collapsed")
    l_file = l_cam if l_cam else l_up

    st.markdown('<div class="dash-header">📸 2. Capture Fault (Image or Video)</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Record video or take photos of the physical issue. You can upload multiple files.</div>', unsafe_allow_html=True)
    
    f_cam = st.camera_input("Capture Fault", key="f_cam", label_visibility="collapsed")
    f_up = st.file_uploader("Upload Media", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"], key="f_up", accept_multiple_files=True, label_visibility="collapsed")
    
    fault_files_to_process = []
    if f_cam:
        fault_files_to_process.append(f_cam)
    if f_up:
        fault_files_to_process.extend(f_up)
    
    ready_for_analysis = bool(l_file and fault_files_to_process)
    
    current_label_name = getattr(l_file, 'name', None) if l_file else None
    current_fault_names = [getattr(f, 'name', 'camera_capture') for f in fault_files_to_process]

    if current_label_name != st.session_state.last_label_name or current_fault_names != st.session_state.last_fault_names:
        st.session_state.last_label_name = current_label_name
        st.session_state.last_fault_names = current_fault_names
        st.session_state.analysis_done = False
        st.session_state.force_escalated = False
        st.session_state.analysis_results = {}

    if ready_for_analysis:
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1]) 
        
        with col2: 
            if st.button("START DIAGNOSTIC", type="primary", use_container_width=True):
                st.session_state.force_escalated = False 
                with st.spinner("Processing..."):
                    label_img = Image.open(l_file).convert("RGB")
                    
                    buffered_l = io.BytesIO()
                    label_img.save(buffered_l, format="JPEG")
                    img_str_l = base64.b64encode(buffered_l.getvalue()).decode("ascii")
                    url = f"https://detect.roboflow.com/{MODEL_ENDPOINT}?api_key={API_KEY}&confidence=25"
                    
                    try:
                        resp_l = requests.post(url, data=img_str_l, headers={"Content-Type": "application/x-www-form-urlencoded"})
                        preds_l = resp_l.json().get('predictions', [])
                    except:
                        preds_l = []
                    
                    brand, model, serial = "Proton eMAS", "Unknown", "Not detected"
                    for p in preds_l:
                        x0, y0, x1, y1 = p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2
                        if p['class'] == "model_name":
                            roi = np.array(label_img.crop((x0, y0, x1, y1)))
                            res = reader.readtext(roi, detail=0)
                            if res: model = res[0]
                        elif p['class'] == "serial_number":
                            roi = np.array(label_img.crop((x0, y0, x1, y1)))
                            res = reader.readtext(roi, detail=0)
                            if res: serial = res[0]

                    all_cust_iss = []
                    all_tech_iss = []
                    all_routed_tickets = []
                    annotated_images = []

                    for f_file in fault_files_to_process:
                        if hasattr(f_file, 'type') and f_file.type.startswith('video'):
                            fault_img = get_frame_from_video(f_file)
                        else:
                            fault_img = Image.open(f_file).convert("RGB")

                        if fault_img:
                            buffered_f = io.BytesIO()
                            fault_img.save(buffered_f, format="JPEG")
                            img_str_f = base64.b64encode(buffered_f.getvalue()).decode("ascii")
                            try:
                                resp_f = requests.post(url, data=img_str_f, headers={"Content-Type": "application/x-www-form-urlencoded"})
                                preds_f = resp_f.json().get('predictions', [])
                            except:
                                preds_f = []
                            
                            draw = ImageDraw.Draw(fault_img)
                            for p in preds_f:
                                lbl = normalize_label(p['class'])
                                if lbl in ROUTING_LOGIC:
                                    x0, y0 = p['x'] - p['width']/2, p['y'] - p['height']/2
                                    x1, y1 = p['x'] + p['width']/2, p['y'] + p['height']/2
                                    draw.rectangle([x0, y0, x1, y1], outline="#EF4444", width=6) 
                                    route = ROUTING_LOGIC[lbl]
                                    
                                    if route['recipient'] == "Customer":
                                        if lbl not in [i[0] for i in all_cust_iss]:
                                            all_cust_iss.append((lbl, route))
                                    else:
                                        if lbl not in [i[0] for i in all_tech_iss]:
                                            all_tech_iss.append((lbl, route))
                                            
                                            encoded_img = image_to_base64(fault_img)
                                            current_tickets = load_tickets()
                                            rt_fallback = {"steps": route['steps'], "act": route['act'], "id": route['id'], "severity": route.get('severity', 'High')}
                                            new_ticket = create_routing_ticket(getattr(f_file, 'name', 'upload'), brand, model, serial, lbl, rt_fallback, encoded_img)
                                            
                                            current_tickets.append(new_ticket)
                                            all_routed_tickets.append(new_ticket)
                                            save_tickets(current_tickets)

                            annotated_images.append(fault_img)

                    st.session_state.analysis_results = {
                        'brand': brand, 'model': model, 'serial': serial,
                        'customer_issues': all_cust_iss, 'technician_issues': all_tech_iss,
                        'annotated_fault_images': annotated_images,
                        'routed_tickets': all_routed_tickets
                    }
                    st.session_state.analysis_done = True

    if st.session_state.analysis_done:
        res = st.session_state.analysis_results
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="dash-header">DIAGNOSTIC REPORT</div>', unsafe_allow_html=True)
        
        with st.container(border=True):
            display_serial = res['serial']
            if display_serial.lower().startswith('sn:'): display_serial = display_serial[3:].strip()
            elif display_serial.lower().startswith('sn '): display_serial = display_serial[3:].strip()
            elif display_serial.lower().startswith('sn'): display_serial = display_serial[2:].strip()

            st.markdown(f"<span style='color:#0EA5E9; font-weight:800; font-size:12px;'>DEVICE DETAILS</span><br><b>{res['brand']} / {res['model']}</b><br><span style='color:#94A3B8; font-size:13px; font-weight: 500;'>Serial Number: {display_serial}</span>", unsafe_allow_html=True)
            
        for img in res['annotated_fault_images']:
            st.image(img, use_container_width=True)
        
        # --- NO FAULTS / MANUAL ESCALATION HANDLING ---
        if not res['customer_issues'] and not res['technician_issues']:
            if not st.session_state.force_escalated:
                st.markdown("""
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 12px; padding: 20px; text-align: center; margin-top: 20px;">
                        <p style="color: #10B981; font-weight: 800; font-size: 18px; letter-spacing: 1px; margin: 0; text-align: center;">NO ANOMALIES DETECTED</p>
                        <p style="color: #94A3B8; font-size: 12px; margin-top: 5px; text-align: center;">The scan did not identify any known faults requiring action.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; font-size:12px; color:#94A3B8;'>Still experiencing issues?</p>", unsafe_allow_html=True)
                
                btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
                with btn_col2:
                    if st.button("REQUEST MANUAL REVIEW", key="force_esc", use_container_width=True):
                        route_fallback = {
                            "id": "Unknown", 
                            "steps": "Manual diagnostic required. System failed to auto-detect fault.", 
                            "act": "Dispatch Technician for manual inspection.", 
                            "severity": "Unknown"
                        }
                        
                        fallback_img_data = None
                        if res['annotated_fault_images']:
                             fallback_img_data = image_to_base64(res['annotated_fault_images'][0])
                             
                        new_ticket = create_routing_ticket("User Upload", res['brand'], res['model'], display_serial, "UNDIAGNOSED_FAULT", route_fallback, fallback_img_data)
                        
                        current_tickets = load_tickets()
                        current_tickets.append(new_ticket)
                        save_tickets(current_tickets)
                        
                        st.session_state.force_escalated = True
                        res['technician_issues'].append(("UNDIAGNOSED_FAULT", route_fallback))
                        st.rerun()
        
        # --- FIX: Handling Customer vs Technician Logic properly ---
        
        # 1. Show Customer Issues (Self-Resolvable)
        if res['customer_issues']:
            st.markdown("""
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; border-radius: 12px; padding: 15px; text-align: center; margin-top: 20px; margin-bottom: 10px;">
                    <p style="color: #F59E0B; font-weight: 800; font-size: 14px; letter-spacing: 1px; margin: 0;">USER-RESOLVABLE ISSUE DETECTED</p>
                    <p style="color: #94A3B8; font-size: 11px; margin-top: 2px; margin-bottom: 0;">No technician has been dispatched yet. Please follow the steps below.</p>
                </div>
            """, unsafe_allow_html=True)
            
            for lbl, rt in res['customer_issues']:
                with st.expander(f"⚠️ REQUIRED USER ACTION", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown('<p class="data-label">OBSERVATION</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="data-value">{lbl.replace("_"," ").title()}</p>', unsafe_allow_html=True)
                    with c2:
                        st.markdown('<p class="data-label">SEVERITY</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="data-value" style="color:#F59E0B;">{rt.get("severity", "Medium")}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{rt["steps"]}</p>', unsafe_allow_html=True)
            
            # Allow user to escalate if their fix fails
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; font-size:12px; color:#94A3B8;'>Did the steps above fail to fix the issue?</p>", unsafe_allow_html=True)
            bc1, bc2, bc3 = st.columns([1, 2, 1])
            with bc2:
                if st.button("TROUBLESHOOTING FAILED - REQUEST TECHNICIAN", key="esc_cust", use_container_width=True):
                    # Take the first customer issue and force create a ticket
                    lbl, rt = res['customer_issues'][0]
                    fallback_img_data = image_to_base64(res['annotated_fault_images'][0]) if res['annotated_fault_images'] else None
                    new_ticket = create_routing_ticket("User Escalation", res['brand'], res['model'], display_serial, lbl, rt, fallback_img_data)
                    
                    current_tickets = load_tickets()
                    current_tickets.append(new_ticket)
                    save_tickets(current_tickets)
                    
                    st.session_state.force_escalated = True
                    st.rerun()

        # 2. Show Technician Notification (If escalated automatically or manually)
        if res['technician_issues'] or st.session_state.force_escalated:
            
            st.markdown("""
                <div style="background: rgba(14, 165, 233, 0.1); border: 1px solid #0EA5E9; border-radius: 12px; padding: 20px; text-align: center; margin-top: 20px;">
                    <p style="color: #0EA5E9; font-weight: 800; font-size: 18px; letter-spacing: 1px; margin: 0; text-align: center;">MAINTENANCE DISPATCHED</p>
                    <p style="color: #94A3B8; font-size: 12px; margin-top: 5px; text-align: center;">Our technical team has been notified. A service ticket has been created for your unit.</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Show the Ticket ID to the user so they can track it in Tab 2
            if res['routed_tickets']:
                t_id = res['routed_tickets'][-1]['ticket_id']
                st.markdown(f"<p style='text-align:center; margin-top:15px; color:#F8FAFC;'>Your Ticket ID is: <b style='color:#0EA5E9; font-size:18px;'>{t_id}</b></p>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; font-size:12px; color:#94A3B8;'>You can check the progress of this ticket in the 'CHECK STATUS' tab.</p>", unsafe_allow_html=True)


# --- NEW: TAB 2: USER TICKET TRACKING ---
with tab2:
    st.markdown('<div class="dash-header">TRACK YOUR TICKET</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Enter your Ticket ID below to check the current status of your service request.</div>', unsafe_allow_html=True)
    
    search_id = st.text_input("Ticket ID", placeholder="e.g., 20260514000001", label_visibility="collapsed")
    
    if st.button("CHECK STATUS", type="primary"):
        all_tickets = load_tickets()
        found_ticket = next((t for t in all_tickets if t['ticket_id'] == search_id.strip()), None)
        
        if not found_ticket:
            st.error("Ticket not found. Please check the ID and try again.")
        else:
            st.markdown("<hr style='border-color: #1E293B; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            
            # Determine timeline states
            stat = found_ticket['status']
            p_class = "timeline-active" if stat == "Pending Review" else "timeline-resolved" if stat in ["In Progress", "Resolved"] else "timeline-inactive"
            i_class = "timeline-active" if stat == "In Progress" else "timeline-resolved" if stat == "Resolved" else "timeline-inactive"
            r_class = "timeline-active" if stat == "Resolved" else "timeline-inactive"
            
            # Display timeline
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="timeline-box {p_class}">PENDING</div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="timeline-box {i_class}">IN PROGRESS</div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="timeline-box {r_class}">RESOLVED</div>', unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown(f"<span style='color:#0EA5E9; font-weight:800; font-size:12px;'>TICKET DETAILS</span><br><b style='font-size: 18px;'>{found_ticket['observation']}</b>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:#94A3B8; font-size:13px;'>Device: {found_ticket['brand']} / {found_ticket['model']} (SN: {found_ticket['serial']})</span>", unsafe_allow_html=True)
                
                if 'timestamp' in found_ticket:
                    formatted_time = datetime.fromisoformat(found_ticket['timestamp']).strftime('%B %d, %Y - %H:%M %p')
                    st.markdown(f"<span style='color:#64748B; font-size:11px;'>Logged on: {formatted_time}</span>", unsafe_allow_html=True)


# --- 7. TAB 3: ACTIVE SERVICE TICKETS (TECHNICIAN) ---
with tab3:
    all_tickets = load_tickets()
    active_tickets = [t for t in all_tickets if t.get('status') in ["Pending Review", "In Progress"]]
    
    if not active_tickets:
        st.markdown("<br><br><p style='text-align:center; color:#94A3B8; font-weight:800;'>SYSTEM OPTIMAL. NO ACTIVE TICKETS.</p>", unsafe_allow_html=True)
    else:
        in_progress_count = len([t for t in active_tickets if t.get('status') == "In Progress"])
        
        st.markdown("""
            <div style="background: #09090B; border: 1px solid #1E293B; border-radius: 16px; padding: 20px; display: flex; justify-content: space-around; text-align: center; margin-bottom: 20px;">
                <div>
                    <span style="font-size: 24px; font-weight: 800; color: #F8FAFC;">{total}</span><br>
                    <span style="font-size: 10px; color: #64748B; letter-spacing: 2px;">TOTAL TICKETS</span>
                </div>
                <div>
                    <span style="font-size: 24px; font-weight: 800; color: #0EA5E9;">{in_prog}</span><br>
                    <span style="font-size: 10px; color: #64748B; letter-spacing: 2px;">IN PROGRESS</span>
                </div>
            </div>
        """.format(total=len(active_tickets), in_prog=in_progress_count), unsafe_allow_html=True)
        
        st.markdown('<div class="dash-sub" style="margin-bottom: 5px !important;">FILTER BY</div>', unsafe_allow_html=True)
        
        available_dates = sorted(list(set([datetime.fromisoformat(t['timestamp']).date() for t in active_tickets if 'timestamp' in t])), reverse=True)
        available_teams = sorted(list(set([f"{t.get('team_id', '')} - {TEAM_DESCRIPTIONS.get(t.get('team_id', ''), 'Team')}" for t in active_tickets])))
        
        fc1, fc2 = st.columns(2)
        with fc1:
            selected_dates = st.multiselect("Date", available_dates, default=[], label_visibility="collapsed", placeholder="Select Date(s)...")
        with fc2:
            selected_teams = st.multiselect("Department", available_teams, default=[], label_visibility="collapsed", placeholder="Select Department(s)...")
            
        st.markdown("<hr style='border-color: #1E293B; margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        filtered_tickets = []
        for t in active_tickets:
            try:
                ticket_date = datetime.fromisoformat(t['timestamp']).date()
                date_match = (len(selected_dates) == 0) or (ticket_date in selected_dates)
            except:
                date_match = True 
                
            ticket_team_string = f"{t.get('team_id', '')} - {TEAM_DESCRIPTIONS.get(t.get('team_id', ''), 'Team')}"
            team_match = (len(selected_teams) == 0) or (ticket_team_string in selected_teams)
            
            if date_match and team_match:
                filtered_tickets.append(t)
        
        st.markdown('<div class="dash-header" style="margin-top: 0px !important;">ACTIVE TICKETS</div>', unsafe_allow_html=True)
        
        if not filtered_tickets:
            st.markdown("<p style='text-align:center; color:#94A3B8; margin-top:20px;'>No tickets match the selected filters.</p>", unsafe_allow_html=True)
            
        for idx, ticket in enumerate(filtered_tickets):
            status_color = "#EF4444" if ticket['status'] == "Pending Review" else "#0EA5E9" if ticket['status'] == "In Progress" else "#10B981"
            
            if ticket.get('team_id') == "Unknown":
                team_desc = "Manual Review Required"
            else:
                team_desc = TEAM_DESCRIPTIONS.get(ticket.get('team_id', ''), f"Team {ticket.get('team_id', '')}")
            
            with st.expander(f"🎫 TICKET {ticket['ticket_id']} — {ticket['observation']}"):
                
                header_col1, header_col2 = st.columns([1, 1])
                with header_col1:
                    st.markdown(f'<span style="background-color: {status_color}; color: #000000; padding: 4px 12px; border-radius: 4px; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform:uppercase;">{ticket["status"]}</span>', unsafe_allow_html=True)
                with header_col2:
                    if 'timestamp' in ticket:
                        try:
                            formatted_time = datetime.fromisoformat(ticket['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                            st.markdown(f'<p style="color: #64748B; font-size: 11px; text-align: right; margin-top: 5px;">Logged: {formatted_time}</p>', unsafe_allow_html=True)
                        except: pass
                
                st.markdown("<hr style='border-color: #1E293B; margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                
                if ticket.get("image_data"):
                    try:
                        decoded_img = base64_to_image(ticket["image_data"])
                        st.markdown('<p class="data-label">DIAGNOSTIC CAPTURE</p>', unsafe_allow_html=True)
                        st.image(decoded_img, use_container_width=True)
                    except: pass
                
                display_serial_t2 = ticket["serial"]
                if display_serial_t2.lower().startswith('sn:'): display_serial_t2 = display_serial_t2[3:].strip()
                elif display_serial_t2.lower().startswith('sn '): display_serial_t2 = display_serial_t2[3:].strip()
                elif display_serial_t2.lower().startswith('sn'): display_serial_t2 = display_serial_t2[2:].strip()

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<p class="data-label">UNIT IDENTIFICATION</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{ticket["brand"]} / {ticket["model"]}<br><span style="color:#94A3B8; font-size:13px; font-weight: 500;">Serial Number: {display_serial_t2}</span></p>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<p class="data-label">RECIPIENT</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{ticket.get("team_id", "")} - {team_desc}</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{ticket["troubleshooting_steps"]}</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value" style="color:#EF4444;">{ticket["action_required"]}</p>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                btn_c1, btn_c2 = st.columns(2)
                tid = ticket['ticket_id']
                
                with btn_c1:
                    if st.button("MARK IN PROGRESS", key=f"p_{tid}_{idx}", use_container_width=True):
                        current_t = load_tickets()
                        for item in current_t:
                            if item['ticket_id'] == tid: item['status'] = "In Progress"
                        save_tickets(current_t); st.rerun()
                
                with btn_c2:
                    if st.button("RESOLVE TICKET", key=f"r_{tid}_{idx}", use_container_width=True):
                        current_t = load_tickets()
                        for item in current_t:
                            if item['ticket_id'] == tid: item['status'] = "Resolved"
                        save_tickets(current_t); st.rerun()

# --- 8. TAB 4: RESOLVED TICKET HISTORY (TECHNICIAN) ---
with tab4:
    all_tickets = load_tickets()
    
    resolved_tickets = [t for t in all_tickets if t.get('status') == "Resolved"]
    
    if not resolved_tickets:
        st.markdown("<br><br><p style='text-align:center; color:#94A3B8; font-weight:800;'>NO RESOLVED TICKETS FOUND.</p>", unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background: #09090B; border: 1px solid #10B981; border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px;">
                <span style="font-size: 32px; font-weight: 800; color: #10B981;">{total}</span><br>
                <span style="font-size: 12px; color: #64748B; letter-spacing: 2px;">TOTAL RESOLVED</span>
            </div>
        """.format(total=len(resolved_tickets)), unsafe_allow_html=True)
        
        st.markdown('<div class="dash-sub" style="margin-bottom: 5px !important;">FILTER HISTORY BY</div>', unsafe_allow_html=True)
        
        available_dates_hist = sorted(list(set([datetime.fromisoformat(t['timestamp']).date() for t in resolved_tickets if 'timestamp' in t])), reverse=True)
        available_teams_hist = sorted(list(set([f"{t.get('team_id', '')} - {TEAM_DESCRIPTIONS.get(t.get('team_id', ''), 'Team')}" for t in resolved_tickets])))
        
        fc1_h, fc2_h = st.columns(2)
        with fc1_h:
            selected_dates_hist = st.multiselect("Date", available_dates_hist, default=[], key="date_hist", label_visibility="collapsed", placeholder="Select Date(s)...")
        with fc2_h:
            selected_teams_hist = st.multiselect("Department", available_teams_hist, default=[], key="dept_hist", label_visibility="collapsed", placeholder="Select Department(s)...")
            
        st.markdown("<hr style='border-color: #1E293B; margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        filtered_history = []
        for t in resolved_tickets:
            try:
                ticket_date = datetime.fromisoformat(t['timestamp']).date()
                date_match = (len(selected_dates_hist) == 0) or (ticket_date in selected_dates_hist)
            except:
                date_match = True 
                
            ticket_team_string = f"{t.get('team_id', '')} - {TEAM_DESCRIPTIONS.get(t.get('team_id', ''), 'Team')}"
            team_match = (len(selected_teams_hist) == 0) or (ticket_team_string in selected_teams_hist)
            
            if date_match and team_match:
                filtered_history.append(t)
        
        st.markdown('<div class="dash-header" style="margin-top: 0px !important;">ARCHIVED TICKETS</div>', unsafe_allow_html=True)
        
        if not filtered_history:
            st.markdown("<p style='text-align:center; color:#94A3B8; margin-top:20px;'>No history matches the selected filters.</p>", unsafe_allow_html=True)
            
        for idx, ticket in enumerate(filtered_history):
            if ticket.get('team_id') == "Unknown":
                team_desc = "Manual Review Required"
            else:
                team_desc = TEAM_DESCRIPTIONS.get(ticket.get('team_id', ''), f"Team {ticket.get('team_id', '')}")
            
            with st.expander(f"✅ TICKET {ticket['ticket_id']} — {ticket['observation']}"):
                
                header_col1, header_col2 = st.columns([1, 1])
                with header_col1:
                    st.markdown(f'<span style="background-color: #10B981; color: #000000; padding: 4px 12px; border-radius: 4px; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform:uppercase;">RESOLVED</span>', unsafe_allow_html=True)
                with header_col2:
                    if 'timestamp' in ticket:
                        try:
                            formatted_time = datetime.fromisoformat(ticket['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                            st.markdown(f'<p style="color: #64748B; font-size: 11px; text-align: right; margin-top: 5px;">Logged: {formatted_time}</p>', unsafe_allow_html=True)
                        except: pass
                
                st.markdown("<hr style='border-color: #1E293B; margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                
                if ticket.get("image_data"):
                    try:
                        decoded_img = base64_to_image(ticket["image_data"])
                        st.markdown('<p class="data-label">DIAGNOSTIC CAPTURE</p>', unsafe_allow_html=True)
                        st.image(decoded_img, use_container_width=True)
                    except: pass
                
                display_serial_t3 = ticket["serial"]
                if display_serial_t3.lower().startswith('sn:'): display_serial_t3 = display_serial_t3[3:].strip()
                elif display_serial_t3.lower().startswith('sn '): display_serial_t3 = display_serial_t3[3:].strip()
                elif display_serial_t3.lower().startswith('sn'): display_serial_t3 = display_serial_t3[2:].strip()

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<p class="data-label">UNIT IDENTIFICATION</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{ticket["brand"]} / {ticket["model"]}<br><span style="color:#94A3B8; font-size:13px; font-weight: 500;">Serial Number: {display_serial_t3}</span></p>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<p class="data-label">RECIPIENT</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{ticket.get("team_id", "")} - {team_desc}</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{ticket["troubleshooting_steps"]}</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value" style="color:#10B981;">{ticket["action_required"]}</p>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                tid = ticket['ticket_id']
                
                if st.button("DELETE RECORD", key=f"del_{tid}_{idx}", use_container_width=True):
                    current_t = [item for item in load_tickets() if item['ticket_id'] != tid]
                    save_tickets(current_t); st.rerun()