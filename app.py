import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw
import io
import numpy as np
import easyocr
import re
import csv
import json
from datetime import datetime
from pathlib import Path

# --- 1. SETUP & DATA LOADING ---
st.set_page_config(page_title="RExharge Diagnostic Hub", page_icon="⚡", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- SESSION STATE SETUP ---
if 'last_label_name' not in st.session_state:
    st.session_state.last_label_name = None
    st.session_state.last_fault_name = None
    st.session_state.analysis_done = False
    st.session_state.analysis_results = {}

# --- ROUTING TICKET SYSTEM ---
TICKETS_FILE = "routing_tickets.json"

def load_tickets():
    """Load routing tickets for after-sales team"""
    if Path(TICKETS_FILE).exists():
        with open(TICKETS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_tickets(tickets):
    """Save routing tickets"""
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

# Helper to show boxed error panels consistently
def boxed_error(message, title="Error"):
    styled_message = message.replace("\n", "<br>")
    st.markdown(
        f"""
        <div style='border:1px solid #fa4c4c; border-radius:10px; padding:16px; background:#fff0f0; color:#9d1a1a; margin:12px 0;'>
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


def create_routing_ticket(file_name, brand, model, serial, fault_label, route_info, image_data=None):
    """Create a ticket to route to after-sales team"""
    # Generate ticket ID as YYYYMMDD + sequential number
    today = datetime.now().strftime('%Y%m%d')
    existing_tickets = load_tickets()
    
    # Find the highest sequential number for today
    today_tickets = [t for t in existing_tickets if t['ticket_id'].startswith(today)]
    if today_tickets:
        # Extract sequential numbers and find the max
        sequential_nums = []
        for ticket in today_tickets:
            try:
                seq_num = int(ticket['ticket_id'][8:])  # After YYYYMMDD
                sequential_nums.append(seq_num)
            except (ValueError, IndexError):
                continue
        next_seq = max(sequential_nums) + 1 if sequential_nums else 1
    else:
        next_seq = 1
    
    ticket_id = f"{today}{next_seq:06d}"  # Format as YYYYMMDD000001
    
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
            # Determine recipient based on action text
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

# Team Descriptions
TEAM_DESCRIPTIONS = {
    "P01": "Electrical & Utility - Power Supply Issues",
    "P02": "Hardware Failure - Critical Component Damage", 
    "P03": "Electrical & Utility - Control Circuit Problems",
    "P04": "Operational - Switch & Control Systems",
    "P05": "Electrical & Utility - Circuit Protection",
    "P06": "Electrical & Utility - Utility Connection Issues",
    "P07": "Electrical & Utility - Fuse & Protection Systems",
    "P08": "Electrical & Utility - Grounding & Firmware Issues",
    "P09": "Electrical & Utility - Over Current Protection"
}

# --- 2. CONFIGURATION ---
API_KEY = "Ho84sOOICvlyZ2T0K60S"
MODEL_ENDPOINT = "rexharge-2026/2" 

# --- 3. TAB NAVIGATION ---
tab1, tab2 = st.tabs(["🔍 Diagnostic Analysis", "📋 After-Sales Tickets"])

# === TAB 1: DIAGNOSTIC ANALYSIS ===
with tab1:
    st.title("⚡ REXharge: Smart Diagnostic Hub")
    
    st.write("Have no idea why your EV charger got problem again? Upload here for instant solutions!")
    
    st.markdown("### 📸 Upload Evidence")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**1️⃣ Charger Label Image**")
        label_file = st.file_uploader("Upload charger label (brand/model/serial):", type=["jpg", "jpeg", "png"], key="label_upload")
    
    with col2:
        st.markdown("**2️⃣ Fault/Issue Image**")
        fault_file = st.file_uploader("Upload charger fault/issue image:", type=["jpg", "jpeg", "png", "mp4", "mov"], key="fault_upload")
    
    # Require both files before analysis, but do not stop the whole script so tab2 remains available
    ready_for_analysis = bool(label_file and fault_file)
    current_label_name = label_file.name if label_file else None
    current_fault_name = fault_file.name if fault_file else None

    if current_label_name != st.session_state.last_label_name or current_fault_name != st.session_state.last_fault_name:
        st.session_state.last_label_name = current_label_name
        st.session_state.last_fault_name = current_fault_name
        st.session_state.analysis_done = False
        st.session_state.analysis_results = {}

    if not ready_for_analysis:
        st.info("📋 Please upload both charger label image and fault/issue image to start analysis.")

    if ready_for_analysis:
        if not st.session_state.analysis_done:
            # Extract brand/model and serial from label image
            brand, model, serial = "", "Unknown", "Not detected"
            label_image = Image.open(label_file).convert("RGB")

            with st.spinner(f"Extracting brand, model, and serial from {label_file.name}..."):
                buffered = io.BytesIO()
                label_image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
                
                url = f"https://detect.roboflow.com/{MODEL_ENDPOINT}?api_key={API_KEY}&confidence=25"
                try:
                    response = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
                    response.raise_for_status()
                    predictions = response.json().get('predictions', [])
                except requests.exceptions.RequestException as exc:
                    boxed_error(
                        "Unable to contact the Roboflow service. Please check your network connection and try again.\n"
                        f"Details: {exc}"
                    )
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

            fault_image = Image.open(fault_file).convert("RGB")
            
            with st.spinner(f"Analyzing {fault_file.name}..."):
                buffered = io.BytesIO()
                fault_image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
                
                url = f"https://detect.roboflow.com/{MODEL_ENDPOINT}?api_key={API_KEY}&confidence=25"
                try:
                    response = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
                    response.raise_for_status()
                    predictions = response.json().get('predictions', [])
                except requests.exceptions.RequestException as exc:
                    boxed_error(
                        "Unable to contact the Roboflow service. Please check your network connection and try again.\n"
                        f"Details: {exc}"
                    )
                    predictions = []

                draw = ImageDraw.Draw(fault_image)
                faults_to_show = []
                for p in predictions:
                    raw_label = p['class']
                    label = normalize_label(raw_label)
                    x0, y0, x1, y1 = p['x']-p['width']/2, p['y']-p['height']/2, p['x']+p['width']/2, p['y']+p['height']/2
                    if label in ROUTING_LOGIC:
                        draw.rectangle([x0, y0, x1, y1], outline="red", width=12)
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
                        fault_file.name, brand, model, serial, label, route
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
                'fault_file_name': fault_file.name
            }
            st.session_state.analysis_done = True

        results = st.session_state.analysis_results
        st.divider()
        st.subheader("Results:")
        display_id = f"{results.get('brand', '')} / {results.get('model', 'Unknown')}" if results.get('brand') else results.get('model', 'Unknown')
        st.info(f"**Brand / Model:** {display_id}")
        st.info(f"**Serial Number:** {results.get('serial', 'Not detected')}")

        st.divider()
        st.subheader("Analysis:")

        if results.get('customer_issues') or results.get('technician_issues'):
            if results.get('customer_issues'):
                st.markdown("### 👤 Actions for You (Customer)")
                for label, route in results['customer_issues']:
                    with st.container(border=True):
                        st.markdown(f"#### 🔍 **Observation:** {label.replace('_', ' ').title()}")
                        st.markdown(f"**Severity:** `{route['severity']}` | **Category:** `{route['category']}`")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**📝 Troubleshooting Steps:**")
                            st.markdown(route['steps'])
                        with col2:
                            st.markdown("**✅ What You Should Do:**")
                            st.markdown(route['act'])
            if results.get('technician_issues'):
                st.markdown("### 🔧 Escalated to After-Sales Team")
                for index, (label, route) in enumerate(results['technician_issues']):
                    ticket = results['routed_tickets'][index] if index < len(results['routed_tickets']) else None
                    ticket_id = ticket['ticket_id'] if ticket else "N/A"
                    team_desc = TEAM_DESCRIPTIONS.get(route['id'], f"Team {route['id']}")
                    with st.container(border=True):
                        st.markdown(f"#### 🚨 **Observation:** {label.replace('_', ' ').title()}")
                        st.markdown(f"**Severity:** `{route['severity']}` | **Category:** `{route['category']}`")
                        info_col1, info_col2 = st.columns([2, 1])
                        with info_col1:
                            st.metric("Ticket ID", ticket_id)
                            st.metric("Recipient", f"{route['id']} - {team_desc}")
                        with info_col2:
                            st.metric("Status", "🟡 Pending Review")
                        st.markdown("**📋 Troubleshooting Steps (for technician):**")
                        st.code(route['steps'])
                        st.markdown("**⚙️ Required Actions:**")
                        st.code(route['act'])
        else:
            st.info("✅ No fault labels were detected in the image. If the issue persists, please re-upload a clearer image or contact support.")

        st.markdown("### 📷 Analyzed Image")
        st.image(results.get('annotated_fault_image', Image.open(fault_file).convert("RGB")), use_container_width=True)

        if results.get('routed_tickets'):
            ticket_count = len(results['routed_tickets'])
            ticket_ids = [t['ticket_id'] for t in results['routed_tickets']]
            st.success(f"✅ {ticket_count} ticket{'s' if ticket_count > 1 else ''} added to After-Sales Team: {', '.join(ticket_ids)}")

# === TAB 2: AFTER-SALES TEAM DASHBOARD ===
with tab2:
    st.title("📋 After-Sales Team: Ticket Management")
    
    tickets = load_tickets()
    
    if not tickets:
        st.info("📭 No tickets currently in the queue.")
    else:
        st.markdown(f"### Total Tickets: {len(tickets)}")
        
        # Filter options
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            team_filter = st.selectbox(
                "Filter by Team ID:",
                ["All"] + sorted(list(set([t['team_id'] for t in tickets]))),
                key="team_filter"
            )
        with filter_col2:
            status_filter = st.selectbox(
                "Filter by Status:",
                ["All", "Pending Review", "In Progress", "Resolved"],
                key="status_filter"
            )
        
        # Apply filters
        filtered_tickets = tickets
        if team_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t['team_id'] == team_filter]
        if status_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t['status'] == status_filter]
        
        # Display tickets
        for idx, ticket in enumerate(filtered_tickets):
            team_desc = TEAM_DESCRIPTIONS.get(ticket['team_id'], f"Team {ticket['team_id']}")
            with st.expander(f"🎫 {ticket['ticket_id']} | {ticket['observation']} | Team: {ticket['team_id']} - {team_desc}", expanded=False):
                # Ticket header
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Ticket ID", ticket['ticket_id'])
                with col2:
                    team_desc = TEAM_DESCRIPTIONS.get(ticket['team_id'], f"Team {ticket['team_id']}")
                    st.metric("Team ID", f"{ticket['team_id']} - {team_desc}")
                with col3:
                    st.metric("Status", ticket['status'])
                with col4:
                    st.metric("Created", ticket['timestamp'][:10])
                
                st.divider()
                
                # Equipment details
                st.markdown("**📦 Equipment Details:**")
                eq_col1, eq_col2 = st.columns(2)
                with eq_col1:
                    st.write(f"**Brand/Model:** {ticket['brand']} / {ticket['model']}")
                with eq_col2:
                    st.write(f"**Serial:** {ticket['serial']}")
                st.write(f"**File:** {ticket['file_name']}")
                
                st.divider()
                
                # Fault details
                st.markdown("**🔍 Fault Analysis:**")
                st.write(f"**Observation:** {ticket['observation']}")
                
                fault_col1, fault_col2 = st.columns(2)
                with fault_col1:
                    st.markdown("**Troubleshooting Steps:**")
                    st.code(ticket['troubleshooting_steps'], language="text")
                with fault_col2:
                    st.markdown("**Required Actions:**")
                    st.code(ticket['action_required'], language="text")
                
                st.divider()
                
                # Team actions
                st.markdown("**🛠️ Team Actions:**")
                action_col1, action_col2, action_col3 = st.columns(3)
                ticket_key = f"{ticket['ticket_id']}_{idx}"
                ticket_id = ticket['ticket_id']
                with action_col1:
                    if st.button("🔄 Mark In Progress", key=f"progress_{ticket_key}"):
                        ticket_index = next((i for i, t in enumerate(tickets) if t['ticket_id'] == ticket_id), None)
                        if ticket_index is not None:
                            tickets[ticket_index]['status'] = "In Progress"
                            save_tickets(tickets)
                            st.rerun()
                with action_col2:
                    if st.button("✅ Mark Resolved", key=f"resolved_{ticket_key}"):
                        ticket_index = next((i for i, t in enumerate(tickets) if t['ticket_id'] == ticket_id), None)
                        if ticket_index is not None:
                            tickets[ticket_index]['status'] = "Resolved"
                            save_tickets(tickets)
                            st.rerun()
                with action_col3:
                    if st.button("🗑️ Delete Ticket", key=f"delete_{ticket_key}"):
                        ticket_index = next((i for i, t in enumerate(tickets) if t['ticket_id'] == ticket_id), None)
                        if ticket_index is not None:
                            tickets.pop(ticket_index)
                            save_tickets(tickets)
                            st.rerun()