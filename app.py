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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

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
   TITLE
============================== */
h1 {
    color: #7DD3FC !important;
    font-weight: 800 !important;
    text-shadow: 0 0 18px rgba(56,189,248,0.55);
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
   DISABLE BIG RECTANGLE CLICK
============================== */
[data-testid="stFileUploadDropzone"] {
    pointer-events: none !important;
    cursor: default !important;
}

[data-testid="stFileUploadDropzone"] button {
    pointer-events: auto !important;
    cursor: pointer !important;
}

[data-testid="stFileUploadDropzone"] input[type="file"] {
    display: none !important;
    pointer-events: none !important;
}

/* ==============================
   TABS
============================== */
.stTabs [data-baseweb="tab"] p {
    color: #94A3B8 !important;
    font-weight: 700 !important;
}

.stTabs [aria-selected="true"] p {
    color: #F8FAFC !important;
    font-weight: 800 !important;
}

/* ==============================
   CAMERA MESSAGE
============================== */
[data-testid="stCameraInput"] small,
[data-testid="stCameraInput"] span,
[data-testid="stCameraInput"] label,
[data-testid="stCameraInput"] div {
    color: #475569 !important;
    -webkit-text-fill-color: #475569 !important;
    opacity: 1 !important;
}

/* ==============================
   TAKE PHOTO BUTTON
============================== */
[data-testid="stCameraInput"] button,
[data-testid="stCameraInput"] button * {
    color: #38BDF8 !important;
    -webkit-text-fill-color: #38BDF8 !important;
    font-weight: 700 !important;
}

/* ==============================
   UPLOAD BUTTON + TEXT + ICON (FIXED)
============================== */

/* Button */
[data-testid="stFileUploadDropzone"] button,
[data-testid="stFileUploadDropzone"] button * {
    color: #38BDF8 !important;
    -webkit-text-fill-color: #38BDF8 !important;
    font-weight: 700 !important;
}

/* Instruction text (THIS FIXES YOUR ISSUE) */
[data-testid="stFileUploadDropzoneInstructions"],
[data-testid="stFileUploadDropzoneInstructions"] * {
    color: #38BDF8 !important;
    -webkit-text-fill-color: #38BDF8 !important;
    font-weight: 700 !important;
}

/* Icon (SVG) */
[data-testid="stFileUploadDropzoneInstructions"] svg,
[data-testid="stFileUploadDropzoneInstructions"] svg * {
    fill: #38BDF8 !important;
    stroke: #38BDF8 !important;
    color: #38BDF8 !important;
}

/* ==============================
   UPLOAD INFO TEXT
============================== */
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span {
    color: #94A3B8 !important;
    -webkit-text-fill-color: #94A3B8 !important;
}

/* Uploaded filename */
[data-testid="stFileUploader"] [data-testid="stText"] span,
[data-testid="stFileUploader"] .uploadedFileName {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* ==============================
   BUTTONS INSIDE BOXES
============================== */
[data-testid="stFileUploader"] button,
[data-testid="stCameraInput"] button {
    background-color: #1E293B !important;
    border: 1px solid #0EA5E9 !important;
    border-radius: 8px !important;
}

/* ==============================
   MAIN START BUTTONS
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
}

.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #0284C7, #1E40AF) !important;
    color: #FFFFFF !important;
}

/* ==============================
   INNER CARDS
============================== */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(14, 165, 233, 0.3) !important;
    border-radius: 12px !important;
}

/* ==============================
   CUSTOM TEXT
============================== */
.dash-header {
    font-size: 18px;
    font-weight: 800;
    color: #F8FAFC;
    margin-top: 25px;
}

.dash-sub {
    font-size: 13px;
    color: #94A3B8;
    margin-bottom: 15px;
}

/* ==============================
   DATA LABELS
============================== */
.data-label {
    color: #64748B;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 4px;
    margin-top: 12px;
}

.data-value {
    color: #F8FAFC;
    font-size: 15px;
    font-weight: 600;
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
        "status": "Pending Review",
        "severity": route_info.get('severity', 'High') 
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
    pass 

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
        <h1 style="font-size: 3.5rem; margin-bottom: 0px; background: -webkit-linear-gradient(45deg, #0EA5E9, #FFFFFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 0px 10px rgba(14, 165, 233, 0.3);">⚡ RExharge</h1>
        <p style="color: #38BDF8; letter-spacing: 5px; font-size: 10px; font-weight: 800; margin-top: -10px;">SYSTEM DIAGNOSTIC HUB</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["DIAGNOSTICS", "SYSTEM QUEUE"])

with tab1:
    st.markdown('<div class="dash-header">📸 1. Scan Charger Label</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Take a photo of the brand/model/serial sticker.</div>', unsafe_allow_html=True)
    
    label_camera = st.camera_input("Scanner", key="label_cam", label_visibility="collapsed")
    label_upload = st.file_uploader("Upload Asset", type=["jpg", "jpeg", "png"], key="label_upload", label_visibility="collapsed")
    label_file = label_camera if label_camera else label_upload

    st.markdown('<div class="dash-header">📸 2. Capture Fault (Image or Video)</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Record video or take a photo of the physical issue.</div>', unsafe_allow_html=True)
    
    fault_camera = st.camera_input("Capture", key="fault_cam", label_visibility="collapsed")
    fault_upload = st.file_uploader("Upload Media", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"], key="fault_upload", label_visibility="collapsed")
    fault_file = fault_camera if fault_camera else fault_upload
    
    ready_for_analysis = bool(label_file and fault_file)
    current_label_name = getattr(label_file, 'name', None) if label_file else None
    current_fault_name = getattr(fault_file, 'name', None) if fault_file else None

    if current_label_name != st.session_state.last_label_name or current_fault_name != st.session_state.last_fault_name:
        st.session_state.last_label_name = current_label_name
        st.session_state.last_fault_name = current_fault_name
        st.session_state.analysis_done = False
        st.session_state.analysis_results = {}

    if ready_for_analysis:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("START DIAGNOSTIC", type="primary"):
            with st.spinner("Processing..."):
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
                            x0, y0 = p['x'] - p['width']/2, p['y'] - p['height']/2
                            x1, y1 = p['x'] + p['width']/2, p['y'] + p['height']/2
                            draw.rectangle([x0, y0, x1, y1], outline="#EF4444", width=6) 
                            route = ROUTING_LOGIC[lbl]
                            if route['recipient'] == "Customer":
                                cust_iss.append((lbl, route))
                            else:
                                tech_iss.append((lbl, route))

                    routed_tickets = []
                    if tech_iss:
                        current_tickets = load_tickets()
                        for lbl, rt in tech_iss:
                            new_ticket = create_routing_ticket(getattr(fault_file, 'name', 'upload'), brand, model, serial, lbl, rt)
                            current_tickets.append(new_ticket)
                            routed_tickets.append(new_ticket)
                        save_tickets(current_tickets)

                    st.session_state.analysis_results = {
                        'brand': brand, 'model': model, 'serial': serial,
                        'customer_issues': cust_iss, 'technician_issues': tech_iss,
                        'annotated_fault_image': fault_img,
                        'routed_tickets': routed_tickets
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
                team_desc = TEAM_DESCRIPTIONS.get(rt['id'], f"Team {rt['id']}")
                
                with st.expander(f"🚨 ESCALATED PROTOCOL"):
                    st.markdown('<p class="data-label">TICKET ID</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#0EA5E9; font-weight:800;">{ticket_id}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">OBSERVATION</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{lbl.replace("_"," ").title()}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">SEVERITY</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#EF4444;">{rt.get("severity", "High")}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">RECIPIENT</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{rt["id"]} - {team_desc}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{rt["steps"]}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#EF4444;">{rt["act"]}</p>', unsafe_allow_html=True)

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
            team_desc = TEAM_DESCRIPTIONS.get(ticket['team_id'], f"Team {ticket['team_id']}")
            
            with st.expander(f"🎫 TICKET {ticket['ticket_id']} — {ticket['observation']}"):
                st.markdown(f'<span style="background-color: {status_color}; color: #000000; padding: 4px 12px; border-radius: 4px; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform:uppercase;">{ticket["status"]}</span>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">UNIT IDENTIFICATION</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{ticket["brand"]} / {ticket["model"]} (SN: {ticket["serial"]})</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">RECIPIENT</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{ticket["team_id"]} - {team_desc}</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">TROUBLESHOOTING STEPS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value">{ticket["troubleshooting_steps"]}</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="data-label">REQUIRED ACTIONS</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="data-value" style="color:#EF4444;">{ticket["action_required"]}</p>', unsafe_allow_html=True)
                
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