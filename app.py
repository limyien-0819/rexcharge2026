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
import tempfile  # Needed for video processing
from datetime import datetime
from pathlib import Path

# --- 1. SETUP & PAGE CONFIGURATION ---
st.set_page_config(page_title="RExharge Smart Diagnostic Hub", page_icon="⚡", layout="centered")

# --- DARK MODE "ATAS" PREMIUM UI DESIGN ---
st.markdown("""
    <style>
    /* 1. Import Premium Tech Font (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0F172A !important;
        color: #E2E8F0 !important;
    }

    /* 2. Hide Streamlit Default Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 3. Global Background - Midnight Slate */
    .stApp {
        background-color: #0F172A; 
    }

    /* 4. Elegant Typography */
    h1 {
        color: #F8FAFC !important;
        font-weight: 700;
        letter-spacing: -1px;
    }
    h3, h4 {
        color: #94A3B8 !important;
        font-weight: 600;
    }

    /* 5. Sleek Pill-Shaped Primary Buttons (Electric Blue) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #38BDF8, #1D4ED8) !important;
        color: white !important;
        border-radius: 50px; /* Fully rounded pill shape */
        padding: 14px 24px;
        border: none;
        box-shadow: 0 10px 15px -3px rgba(56, 189, 248, 0.2);
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(56, 189, 248, 0.3);
    }

    /* 6. Smoked Glassmorphism for Expanders (Cards) */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }

    /* 7. Rounded corners for uploaded images */
    [data-testid="stImage"] img {
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    /* 8. Dark Mode Input File Uploaders */
    [data-testid="stFileUploader"] section {
        border-radius: 16px;
        border: 2px dashed #334155;
        background-color: #1E293B;
    }

    /* 9. Metric & Text Adjustments */
    [data-testid="stMetricValue"] {
        color: #38BDF8 !important;
    }
    .stMarkdown p, .stMarkdown div {
        color: #CBD5E1 !important;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- HELPER: VIDEO TO IMAGE ---
def get_frame_from_video(video_file):
    """Saves video to a temp file and extracts the first frame."""
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

# --- SESSION STATE SETUP ---
if 'last_label_name' not in st.session_state:
    st.session_state.last_label_name = None
    st.session_state.last_fault_name = None
    st.session_state.analysis_done = False
    st.session_state.analysis_results = {}

# --- ROUTING TICKET SYSTEM ---
TICKETS_FILE = "routing_tickets.json"

def load_tickets():
    if Path(TICKETS_FILE).exists():
        with open(TICKETS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

def boxed_error(message, title="Error"):
    styled_message = message.replace("\n", "<br>")
    st.markdown(
        f"""
        <div style='border:1px solid #fa4c4c; border-radius:12px; padding:16px; background:#450a0a; color:#fecaca; margin:12px 0;'>
            <strong>{title}</strong><br>{styled_message}
        </div>
        """,
        unsafe_allow_html=True,
    )

def normalize_label(raw_label):
    normalized = raw_label.strip().lower()
    normalized = re.sub(r'[\s\-]+', '_', normalized)
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    normalized = re.sub(r'_+', '_', normalized)
    return normalized.strip('_')

def create_routing_ticket(file_name, brand, model, serial, fault_label, route_info):
    today = datetime.now().strftime('%Y%m%d')
    existing_tickets = load_tickets()
    
    today_tickets = [t for t in existing_tickets if t['ticket_id'].startswith(today)]
    if today_tickets:
        sequential_nums = []
        for ticket in today_tickets:
            try:
                seq_num = int(ticket['ticket_id'][8:])
                sequential_nums.append(seq_num)
            except (ValueError, IndexError):
                continue
        next_seq = max(sequential_nums) + 1 if sequential_nums else 1
    else:
        next_seq = 1
    
    ticket_id = f"{today}{next_seq:06d}"
    
    ticket = {
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
    return ticket

# Load Routing Logic from CSV
ROUTING_LOGIC = {}
try:
    with open('Dataset - Dataset.csv', mode='r') as f:
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
                "severity": row.get('Severity', 'Medium'),
                "category": row.get('Issue Category', 'Unknown'),
                "fault_id": row.get('Fault ID', '')
            }
except Exception as e:
    boxed_error(f"Error loading CSV: {e}")

TEAM_DESCRIPTIONS = {
    "P01": "Electrical & Utility - Power Supply",
    "P02": "Hardware Failure - Critical Component", 
    "P03": "Electrical & Utility - Control Circuit",
    "P04": "Operational - Switch & Control",
    "P05": "Electrical & Utility - Circuit Protection",
    "P06": "Electrical & Utility - Utility Connection",
    "P07": "Electrical & Utility - Fuse Systems",
    "P08": "Electrical & Utility - Grounding/Firmware",
    "P09": "Electrical & Utility - Over Current"
}

# --- 2. CONFIGURATION ---
API_KEY = st.secrets["ROBOFLOW_API_KEY"]
MODEL_ENDPOINT = st.secrets["ROBOFLOW_MODEL_ENDPOINT"] 

# --- 3. TAB NAVIGATION ---
tab1, tab2 = st.tabs(["🔍 Diagnostics", "📋 Tickets"])

# === TAB 1: DIAGNOSTIC ANALYSIS (MOBILE UI) ===
with tab1:
    st.markdown("<h1 style='text-align: center;'>⚡ RExharge</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #94A3B8; margin-bottom: 30px;'>Smart Diagnostic Hub</h4>", unsafe_allow_html=True)
    
    st.markdown("### 📸 1. Scan Charger Label")
    st.write("Take a photo of the brand/model/serial sticker.")
    label_camera = st.camera_input("Take photo of sticker", key="label_cam", label_visibility="collapsed")
    label_upload = st.file_uploader("Or upload from gallery:", type=["jpg", "jpeg", "png"], key="label_upload")
    label_file = label_camera if label_camera else label_upload

    st.divider()

    st.markdown("### 🎥 2. Capture Fault (Image or Video)")
    st.write("Record video or take a photo of the physical issue.")
    fault_camera = st.camera_input("Take photo of fault", key="fault_cam", label_visibility="collapsed")
    fault_upload = st.file_uploader("Or upload from gallery:", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"], key="fault_upload")
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
        if st.button("🚀 Run Diagnostics", use_container_width=True, type="primary"):
            if not st.session_state.analysis_done:
                brand, model, serial = "", "Unknown", "Not detected"
                label_image = Image.open(label_file).convert("RGB")

                with st.spinner(f"Extracting identity data..."):
                    buffered = io.BytesIO()
                    label_image.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
                    
                    url = f"https://detect.roboflow.com/{MODEL_ENDPOINT}?api_key={API_KEY}&confidence=25"
                    try:
                        response = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
                        response.raise_for_status()
                        predictions = response.json().get('predictions', [])
                    except requests.exceptions.RequestException as exc:
                        boxed_error(f"Roboflow connection failed. Details: {exc}")
                        predictions = []

                    for p in predictions:
                        label = p['class']
                        x0, y0, x1, y1 = p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2
                        
                        if label == "proton_emas_logo":
                            brand = "Proton eMAS"
                        elif label == "model_name":
                            roi_m = np.array(label_image.crop((x0, y0, x1, y1)))
                            res_m = reader.readtext(roi_m, detail=0)
                            if res_m:
                                m_match = re.search(r'(?:name|model)\s*:\s*(.*)', res_m[0], re.IGNORECASE)
                                model = m_match.group(1).strip() if m_match else res_m[0].strip()
                        elif label == "serial_number":
                            roi_s = np.array(label_image.crop((x0, y0, x1, y1)))
                            res_s = reader.readtext(roi_s, detail=0)
                            if res_s:
                                serial = re.sub(r'^(SN|S/N|SN:|S/N:)\s*', '', res_s[0], flags=re.IGNORECASE).strip()
                                serial = serial.lstrip(':').strip()

                with st.spinner(f"Analyzing fault..."):
                    if fault_file.type.startswith('video'):
                        fault_image = get_frame_from_video(fault_file)
                    else:
                        fault_image = Image.open(fault_file).convert("RGB")

                    if fault_image:
                        buffered = io.BytesIO()
                        fault_image.save(buffered, format="JPEG")
                        img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
                        
                        try:
                            response = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
                            response.raise_for_status()
                            predictions = response.json().get('predictions', [])
                        except requests.exceptions.RequestException as exc:
                            boxed_error(f"Roboflow connection failed. Details: {exc}")
                            predictions = []

                        draw = ImageDraw.Draw(fault_image)
                        faults_to_show = []
                        for p in predictions:
                            raw_label = p['class']
                            label = normalize_label(raw_label)
                            x0, y0, x1, y1 = p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2
                            if label in ROUTING_LOGIC:
                                draw.rectangle([x0, y0, x1, y1], outline="#38BDF8", width=8) 
                                faults_to_show.append((label, ROUTING_LOGIC[label]))

                        annotated_fault_image = fault_image.copy()
                        customer_issues = []
                        technician_issues = []
                        for label, route in faults_to_show:
                            if route['recipient'] == "Customer":
                                customer_issues.append((label, route))
                            else:
                                technician_issues.append((label, route))

                        routed_tickets = []
                        if technician_issues:
                            for label, route in technician_issues:
                                ticket = create_routing_ticket(
                                    current_fault_name, brand, model, serial, label, route
                                )
                                routed_tickets.append(ticket)

                        if routed_tickets:
                            existing_tickets = load_tickets()
                            existing_tickets.extend(routed_tickets)
                            save_tickets(existing_tickets)

                        st.session_state.analysis_results = {
                            'brand': brand,
                            'model': model,
                            'serial': serial,
                            'customer_issues': customer_issues,
                            'technician_issues': technician_issues,
                            'faults_to_show': faults_to_show,
                            'routed_tickets': routed_tickets,
                            'annotated_fault_image': annotated_fault_image,
                        }
                        st.session_state.analysis_done = True
                    else:
                        st.error("Failed to extract frame from video.")

    if st.session_state.analysis_done:
        results = st.session_state.analysis_results
        st.divider()
        st.subheader("📊 Diagnostic Report")
        
        display_id = f"{results.get('brand', '')} / {results.get('model', 'Unknown')}" if results.get('brand') else results.get('model', 'Unknown')
        
        with st.container(border=True):
            st.markdown(f"**🔌 Device Info**")
            st.info(f"**Model:** {display_id}\n\n**Serial ID:** `{results.get('serial', 'Not detected')}`")

        st.markdown("### 📷 Scanned Evidence")
        st.image(results.get('annotated_fault_image'), use_container_width=True)

        if results.get('customer_issues') or results.get('technician_issues'):
            if results.get('customer_issues'):
                st.markdown("### 👤 Action Required (User)")
                for label, route in results['customer_issues']:
                    st.warning(f"**Detected:** {label.replace('_', ' ').title()}")
                    with st.expander("🛠️ View Troubleshooting Steps", expanded=True):
                        st.markdown(f"**Severity:** `{route['severity']}`")
                        st.write(route['steps'])
                        st.markdown("**Solution:**")
                        st.success(route['act'])
                        
            if results.get('technician_issues'):
                st.markdown("### 🔧 Escalated Issues")
                for index, (label, route) in enumerate(results['technician_issues']):
                    ticket = results['routed_tickets'][index] if index < len(results['routed_tickets']) else None
                    ticket_id = ticket['ticket_id'] if ticket else "N/A"
                    st.error(f"**Detected:** {label.replace('_', ' ').title()}")
                    with st.expander(f"🎫 View Ticket (ID: {ticket_id})", expanded=False):
                        team_desc = TEAM_DESCRIPTIONS.get(route['id'], f"Team {route['id']}")
                        st.markdown(f"**Routed To:** `{route['id']} - {team_desc}`")
                        st.markdown(f"**Severity:** `{route['severity']}`")
                        st.markdown("**Protocol:**")
                        st.write(route['steps'])
                        st.markdown("**Action Required:**")
                        st.info(route['act'])
        else:
            st.success("✅ System functioning normally. No faults detected in scan.")

        if results.get('routed_tickets'):
            st.success(f"✅ {len(results['routed_tickets'])} ticket(s) automatically dispatched to After-Sales.")

# === TAB 2: AFTER-SALES TEAM DASHBOARD (MOBILE UI) ===
with tab2:
    st.markdown("<h2 style='text-align: center;'>📋 Queue Management</h2>", unsafe_allow_html=True)
    
    tickets = load_tickets()
    
    if not tickets:
        st.info("📭 Inbox zero. No active tickets.")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Active Tickets", len(tickets))
        col2.metric("Critical Issues", len([t for t in tickets if t['status'] == "Pending Review"]))
        
        st.divider()
        
        team_filter = st.selectbox("Filter by Department:", ["All"] + sorted(list(set([t['team_id'] for t in tickets]))))
        status_filter = st.selectbox("Filter by Status:", ["All", "Pending Review", "In Progress", "Resolved"])
        
        filtered_tickets = tickets
        if team_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t['team_id'] == team_filter]
        if status_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t['status'] == status_filter]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        for idx, ticket in enumerate(filtered_tickets):
            team_desc = TEAM_DESCRIPTIONS.get(ticket['team_id'], f"Team {ticket['team_id']}")
            status_color = "#EF4444" if ticket['status'] == "Pending Review" else "#10B981" if ticket['status'] == "Resolved" else "#3B82F6"
            
            with st.expander(f"🎫 {ticket['ticket_id']} | {ticket['observation']}", expanded=False):
                st.markdown(f'<span style="background-color: {status_color}; color: white; padding: 4px 12px; border-radius: 50px; font-size: 11px; font-weight: 700;">{ticket["status"]}</span>', unsafe_allow_html=True)
                st.markdown(f"**Department:** {ticket['team_id']} - {team_desc}")
                
                with st.container(border=True):
                    st.markdown(f"**🔌 Hardware Details**")
                    st.write(f"{ticket['brand']} / {ticket['model']}")
                    st.write(f"Serial: `{ticket['serial']}`")
                
                st.markdown("**🛠️ Protocol Requirements:**")
                st.info(ticket['troubleshooting_steps'])
                st.markdown("**Required Actions:**")
                st.warning(ticket['action_required'])
                
                st.divider()
                
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                ticket_id = ticket['ticket_id']
                
                with btn_col1:
                    if st.button("🏗️ Work", key=f"prog_{ticket_id}_{idx}", use_container_width=True):
                        all_tickets = load_tickets()
                        for t in all_tickets:
                            if t['ticket_id'] == ticket_id: t['status'] = "In Progress"
                        save_tickets(all_tickets); st.rerun()
                
                with btn_col2:
                    if st.button("✅ Done", key=f"res_{ticket_id}_{idx}", use_container_width=True, type="primary"):
                        all_tickets = load_tickets()
                        for t in all_tickets:
                            if t['ticket_id'] == ticket_id: t['status'] = "Resolved"
                        save_tickets(all_tickets); st.rerun()
                
                with btn_col3:
                    if st.button("🗑️ Del", key=f"del_{ticket_id}_{idx}", use_container_width=True):
                        all_tickets = [t for t in load_tickets() if t['ticket_id'] != ticket_id]
                        save_tickets(all_tickets); st.rerun()