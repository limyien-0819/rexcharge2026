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

/* ONLY color the primary cloud SVG in the dropzone area */
div[data-testid="stFileUploadDropzone"] > section > svg,
div[data-testid="stFileUploadDropzone"] > section > svg * {
    fill: #38BDF8 !important;
    stroke: #38BDF8 !important;
    color: #38BDF8 !important;
}

/* ==============================
   FILE INFO TEXT
============================== */
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 400 !important;
}

/* ==============================
   UPLOADED FILE CARD FRAME (WHITE BOX)
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

/* ==============================
   DISABLE DROPZONE CLICK
============================== */
[data-testid="stFileUploadDropzone"] {
    pointer-events: none !important;
}

[data-testid="stFileUploadDropzone"] button {
    pointer-events: auto !important;
}

/* ==============================
   MAIN BUTTONS & CARDS
============================== */
/* General Button Base */
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

/* PREMIUM "ATAS" PRIMARY BUTTON STYLING */
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
    st.session_state.last_fault_names = []
    st.session_state.analysis_done = False
    st.session_state.analysis_results = {}

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

def create_routing_ticket(file_name, brand, model, serial, fault_label, route_info):
    today = datetime.now().strftime('%Y%m%d')
    existing_tickets = load_tickets()
    today_tickets = [t for t in existing_tickets if t['ticket_id'].startswith(today)]
    next_seq = (max([int(t['ticket_id'][8:]) for t in today_tickets if t['ticket_id'][8:].isdigit()] or [0]) + 1)
    ticket_id = f"{today}{next_seq:06d}"
    
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

tab1, tab2 = st.tabs(["DIAGNOSTICS", "SERVICE TICKETS"])

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
        st.session_state.analysis_results = {}

    if ready_for_analysis:
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1]) 
        
        with col2: 
            if st.button("START DIAGNOSTIC", type="primary", use_container_width=True):
                with st.spinner("Processing Telemetry..."):
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
                                            current_tickets = load_tickets()
                                            rt_fallback = {"steps": route['steps'], "act": route['act'], "id": route['id'], "severity": route.get('severity', 'High')}
                                            new_ticket = create_routing_ticket(getattr(f_file, 'name', 'upload'), brand, model, serial, lbl, rt_fallback)
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
            st.markdown(f"<span style='color:#0EA5E9; font-weight:800; font-size:12px;'>DEVICE TELEMETRY</span><br><b>{res['brand']} / {res['model']}</b><br><span style='color:#94A3B8; font-size:12px;'>SN: {res['serial']}</span>", unsafe_allow_html=True)
            
        for img in res['annotated_fault_images']:
            st.image(img, use_container_width=True)
        
        if res['customer_issues']:
            for lbl, rt in res['customer_issues']:
                with st.expander(f"⚠️ REQUIRED USER ACTION", expanded=True):
                    st.markdown('<p class="data-label">OBSERVATION</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{lbl.replace("_"," ").title()}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">SEVERITY</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#F59E0B;">{rt.get("severity", "Medium")}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{rt["steps"]}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#10B981;">{rt["act"]}</p>', unsafe_allow_html=True)

        if res['technician_issues']:
            for index, (lbl, rt) in enumerate(res['technician_issues']):
                ticket = res['routed_tickets'][index] if index < len(res['routed_tickets']) else None
                ticket_id = ticket['ticket_id'] if ticket else "PENDING"
                
                with st.expander(f"🚨 ESCALATED PROTOCOL"):
                    st.markdown('<p class="data-label">TICKET ID</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#0EA5E9; font-weight:800;">{ticket_id}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">OBSERVATION</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{lbl.replace("_"," ").title()}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">SEVERITY</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#EF4444;">{rt.get("severity", "High")}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">RECIPIENT</p>', unsafe_allow_html=True)
                    team_info = "Unknown Team"
                    if 'id' in rt:
                         team_info = f"{rt['id']} - {TEAM_DESCRIPTIONS.get(rt['id'], 'Team')}"
                    st.markdown(f'<p class="data-value">{team_info}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{rt.get("steps", "")}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#EF4444;">{rt.get("act", "")}</p>', unsafe_allow_html=True)

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
        
        # CHANGED SUB-HEADER HERE
        st.markdown('<div class="dash-header">ACTIVE TICKETS</div>', unsafe_allow_html=True)
        
        for idx, ticket in enumerate(filtered):
            status_color = "#EF4444" if ticket['status'] == "Pending Review" else "#0EA5E9" if ticket['status'] == "In Progress" else "#10B981"
            team_desc = TEAM_DESCRIPTIONS.get(ticket.get('team_id', ''), f"Team {ticket.get('team_id', '')}")
            
            with st.expander(f"🎫 TICKET {ticket['ticket_id']} — {ticket['observation']}"):
                st.markdown(f'<span style="background-color: {status_color}; color: #000000; padding: 4px 12px; border-radius: 4px; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform:uppercase;">{ticket["status"]}</span>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">UNIT IDENTIFICATION</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{ticket["brand"]} / {ticket["model"]} (SN: {ticket["serial"]})</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">RECIPIENT</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{ticket.get("team_id", "")} - {team_desc}</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{ticket["troubleshooting_steps"]}</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value" style="color:#EF4444;">{ticket["action_required"]}</p>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                tid = ticket['ticket_id']
                
                # CHANGED BUTTON NAMES HERE
                with c1:
                    if st.button("IN PROGRESS", key=f"p_{tid}_{idx}", use_container_width=True):
                        all_t = load_tickets()
                        for item in all_t:
                            if item['ticket_id'] == tid: item['status'] = "In Progress"
                        save_tickets(all_t); st.rerun()
                
                with c2:
                    if st.button("RESOLVED", key=f"r_{tid}_{idx}", use_container_width=True):
                        all_t = load_tickets()
                        for item in all_t:
                            if item['ticket_id'] == tid: item['status'] = "Resolved"
                        save_tickets(all_t); st.rerun()
                
                with c3:
                    if st.button("DELETE", key=f"d_{tid}_{idx}", use_container_width=True):
                        all_t = [item for item in load_tickets() if item['ticket_id'] != tid]
                        save_tickets(all_t); st.rerun()