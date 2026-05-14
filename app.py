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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');

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
    .stMarkdown:not(:has(h1.gradient-title)),
    .stMarkdown:not(:has(h1.gradient-title)) * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    [data-testid="stMarkdownContainer"]:not(:has(h1.gradient-title)),
    [data-testid="stMarkdownContainer"]:not(:has(h1.gradient-title)) * {
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
       BASE BOXES (NAVY)
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

    /* ==============================
       PRECISION ICON TARGETING
    ============================== */
    /* Target ONLY the Cloud Upload Icon to be Blue */
    [data-testid="stFileUploadDropzone"] > section > svg,
    [data-testid="stFileUploadDropzone"] > section > svg * {
        fill: #38BDF8 !important;
        stroke: #38BDF8 !important;
        color: #38BDF8 !important;
    }

    /* ==============================
       UPLOADED FILE CARD (WHITE BOX FIX)
    ============================== */
    /* 1. Force the file card background to be pure white */
    [data-testid="stFileUploader"] section[role="button"] + div {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }

    /* 2. Force the text inside the white card to be black */
    [data-testid="stFileUploader"] section[role="button"] + div *,
    [data-testid="stFileUploader"] .uploadedFileName {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 700 !important;
    }

    /* 3. Force the "Delete Cross" button inside the card to be Neutral/Grey */
    [data-testid="stFileUploader"] section[role="button"] + div button svg,
    [data-testid="stFileUploader"] section[role="button"] + div button svg * {
        fill: #475569 !important; /* Slate Grey */
        stroke: #475569 !important;
        color: #475569 !important;
    }

    /* ==============================
       FILE INFO TEXT (Outside the card)
    ============================== */
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 400 !important;
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

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(14, 165, 233, 0.3) !important;
        border-radius: 12px !important;
    }

    /* ==============================
       SECTION HEADERS
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
    st.session_state.last_fault_name = None
    st.session_state.analysis_done = False
    st.session_state.analysis_results = {}

TICKETS_FILE = "routing_tickets.json"

def load_tickets():
    if Path(TICKETS_FILE).exists():
        try:
            with open(TICKETS_FILE, 'r') as f:
                return json.loads(f.read()) if f.read() else []
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

# --- 5. API CONFIGURATION ---
API_KEY = st.secrets["ROBOFLOW_API_KEY"]
MODEL_ENDPOINT = st.secrets["ROBOFLOW_MODEL_ENDPOINT"] 

# --- 6. MAIN SYSTEM INTERFACE ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 class="gradient-title">⚡ RExharge</h1>
        <p style="color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; letter-spacing: 5px; font-size: 10px; font-weight: 800; margin-top: -10px;">SYSTEM DIAGNOSTIC HUB</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["DIAGNOSTICS", "SYSTEM QUEUE"])

with tab1:
    # Changed header classes back to .dash-header to apply the bold and larger font size styling
    st.markdown('<div class="dash-header">📸 1. Scan Charger Label</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Take a photo of the brand/model/serial sticker.</div>', unsafe_allow_html=True)
    
    l_cam = st.camera_input("Scanner", key="l_cam", label_visibility="collapsed")
    l_up = st.file_uploader("Upload Label", type=["jpg", "jpeg", "png"], key="l_up", label_visibility="collapsed")
    l_file = l_cam if l_cam else l_up

    # Changed header classes back to .dash-header to apply the bold and larger font size styling
    st.markdown('<div class="dash-header">📸 2. Capture Fault (Image or Video)</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Record video or take a photo of the physical issue.</div>', unsafe_allow_html=True)
    
    f_cam = st.camera_input("Capture", key="f_cam", label_visibility="collapsed")
    f_up = st.file_uploader("Upload Media", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"], key="f_up", label_visibility="collapsed")
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
                            new_ticket = create_routing_ticket(getattr(f_file, 'name', 'upload'), brand, model, serial, lbl, rt)
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
                
                with st.expander(f"🚨 ESCALATED PROTOCOL"):
                    st.markdown('<p class="data-label">TICKET ID</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#0EA5E9; font-weight:800;">{ticket_id}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">OBSERVATION</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value">{lbl.replace("_"," ").title()}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">SEVERITY</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="data-value" style="color:#EF4444;">{rt.get("severity", "High")}</p>', unsafe_allow_html=True)
                    
                    st.markdown('<p class="data-label">RECIPIENT</p>', unsafe_allow_html=True)
                    # Use a fallback string in case the key doesn't exist
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
        
        st.markdown('<div class="dash-header">ACTIVE WORK ORDERS</div>', unsafe_allow_html=True)
        
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