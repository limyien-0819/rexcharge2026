# REcharge Dashboard - System Architecture & Implementation

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard Interface                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Tab 1: Diagnostic Analysis          Tab 2: Tickets     │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                    │                │
│           ▼                                    ▼                │
│  ┌──────────────────┐              ┌────────────────────┐     │
│  │ File Uploader    │              │ Ticket Dashboard   │     │
│  │ (JPG/PNG/MP4)    │              │ - View Tickets     │     │
│  └────────┬─────────┘              │ - Filter by Team   │     │
│           │                        │ - Update Status    │     │
│           ▼                        │ - Delete Tickets   │     │
│  ┌──────────────────────────────┐  └────────────────────┘     │
│  │ AI Detection Engine          │           ▲                 │
│  │ (Roboflow API)               │           │                 │
│  │ Detects faults & metadata    │           │                 │
│  └────────┬─────────────────────┘           │                 │
│           │                                 │                 │
│           ▼                                 │                 │
│  ┌──────────────────────────────┐           │                 │
│  │ CSV Routing Logic Loader     │           │                 │
│  │ ROUTING_LOGIC Dictionary     │           │                 │
│  │ Maps each fault to recipient │           │                 │
│  └────────┬─────────────────────┘           │                 │
│           │                                 │                 │
│           ▼                                 │                 │
│  ┌──────────────────────────────┐           │                 │
│  │ Routing Decision Engine      │           │                 │
│  │ Separates:                   │           │                 │
│  │ - Customer issues            │           │                 │
│  │ - Technician issues          │           │                 │
│  └────────┬─────────────────────┘           │                 │
│           │                                 │                 │
│      ┌────┴──────────────┐                  │                 │
│      │                   │                  │                 │
│      ▼                   ▼                  │                 │
│  ┌─────────┐         ┌──────────┐           │                 │
│  │ Customer│         │Technician│           │                 │
│  │ Display │         │ Ticket   │           │                 │
│  │         │         │ Creation │           │                 │
│  └─────────┘         └────┬─────┘           │                 │
│                           │                 │                 │
│                           ▼                 │                 │
│                    ┌──────────────┐         │                 │
│                    │ routing_      │         │                 │
│                    │ tickets.json  ├─────────┘                 │
│                    │ (Persistence)│                            │
│                    └──────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

### 1. **File Upload & Detection**
```
User uploads image/video
    ↓
Streamlit file_uploader captures file
    ↓
Image is sent to Roboflow API with confidence=25
    ↓
AI returns predictions with:
   - class (label)
   - x, y, width, height (bounding box)
    ↓
Extract metadata:
   - proton_emas_logo → Brand
   - model_name → Model
   - serial_number → Serial
   - fault labels → Detected issues
```

### 2. **Routing Logic Processing**
```
For each detected fault label:
    ↓
Lookup in ROUTING_LOGIC dictionary:
    ↓
Read CSV columns:
   - Detection Label (key for lookup)
   - Action Required (determines recipient)
   - Evidence (Team ID)
   - Troubleshooting Steps & Parameters
   - Severity
   - Issue Category
    ↓
Check if "Technician" in Action Required:
    - YES → Technician route
    - NO → Customer route
```

### 3. **Issue Separation**
```
Faults to Show
    ├─ Customer Issues
    │  ├─ Display troubleshooting steps
    │  ├─ Show action required
    │  └─ No ticket created
    │
    └─ Technician Issues
       ├─ Create routing ticket
       ├─ Display ticket info
       ├─ Save to JSON
       └─ Show on After-Sales tab
```

---

## 🔧 Key Components

### 1. **Ticket Management Functions**

#### `load_tickets()`
```python
Purpose: Load existing tickets from JSON file
Returns: List of ticket dictionaries
File: routing_tickets.json
```

#### `save_tickets(tickets)`
```python
Purpose: Save/update tickets to JSON file
Input: List of ticket dictionaries
Output: JSON file with formatted structure
```

#### `create_routing_ticket(...)`
```python
Purpose: Generate a new ticket for after-sales team
Inputs:
  - file_name: Original uploaded file name
  - brand: Detected device brand
  - model: Detected device model
  - serial: Detected device serial number
  - fault_label: Detected fault identifier
  - route_info: Routing information from CSV
  
Returns: Dictionary with ticket details
  - ticket_id: Auto-generated AST-[timestamp]
  - timestamp: ISO format creation time
  - team_id: Assigned team identifier
  - observation: User-readable fault description
  - troubleshooting_steps: For technician
  - action_required: Specific actions
  - status: Initial status "Pending Review"
```

### 2. **ROUTING_LOGIC Dictionary**

```python
ROUTING_LOGIC = {
    "fault_label_1": {
        "id": "P01",  # Team identifier
        "recipient": "Customer" or "After-Sales Team",
        "steps": "Troubleshooting steps...",
        "act": "Action required...",
        "severity": "Critical/High/Medium/Low",
        "category": "Category name",
        "fault_id": "7kW-01"
    },
    # ... more faults
}
```

### 3. **Recipient Determination Logic**

```python
action_text = row['Action Required'].strip()
recipient = "After-Sales Team" if "Technician" in action_text else "Customer"

Examples:
"Technician: Replace damaged components" → After-Sales Team
"User: Contact TNB..." → Customer
"User/Technician: Check..." → Customer (no pure "Technician")
```

---

## 📋 Display Logic

### For Customers:
```
┌─ 👤 Actions for You (Customer)
│  ├─ 🔍 Observation: [Fault Name]
│  ├─ Severity & Category badges
│  ├─ 📝 Troubleshooting Steps: [Specific steps]
│  └─ ✅ What You Should Do: [Clear actions]
```

### For After-Sales Team:
```
┌─ 🔧 Escalated to After-Sales Team
│  ├─ 🚨 Observation: [Fault Name]
│  ├─ Severity & Category badges
│  ├─ 🎫 Ticket ID: AST-[timestamp]
│  ├─ Team ID: P02 (from Evidence column)
│  ├─ Status: 🟡 Pending Review
│  ├─ 📋 Troubleshooting Steps: [Technical details]
│  └─ ⚙️ Required Actions: [Technician actions]
```

---

## 💾 Persistence Model

### JSON File Structure
```json
routing_tickets.json
├─ [
│  ├─ {
│  │  ├─ "ticket_id": "AST-20260505021234"
│  │  ├─ "timestamp": "2026-05-05T02:12:34.567"
│  │  ├─ "team_id": "P02"
│  │  ├─ "file_name": "image.jpg"
│  │  ├─ "brand": "Proton eMAS"
│  │  ├─ "model": "7kW"
│  │  ├─ "serial": "SN123456"
│  │  ├─ "fault_label": "burnt_mark_issue"
│  │  ├─ "observation": "Burnt Mark Issue"
│  │  ├─ "troubleshooting_steps": "..."
│  │  ├─ "action_required": "..."
│  │  └─ "status": "Pending Review"
│  └─ },
│  └─ { ... more tickets ... }
└─ ]
```

### File Operations:
```
Initial Load:
  app.py starts → ROUTING_LOGIC loaded from CSV

Analysis:
  User uploads file → AI detection → Routing logic applied

Ticket Creation:
  Technician issue detected → create_routing_ticket() called
  → routed_tickets list updated (in-memory)

Persistence:
  After all files processed → if routed_tickets not empty:
    → load existing tickets from JSON
    → extend with new tickets
    → save_tickets() writes to file
    → st.success() notification shown

Retrieval (After-Sales Tab):
  → load_tickets() reads from JSON
  → Display in tab2
  → Filter and actions available
  → Status updates trigger re-run
```

---

## 🔀 Filtering & Search (After-Sales Tab)

### Filter by Team ID
```python
team_filter = st.selectbox(..., ["All"] + sorted(list(set([t['team_id'] for t in tickets]))))
if team_filter != "All":
    filtered_tickets = [t for t in filtered_tickets if t['team_id'] == team_filter]
```
Dynamically shows available teams from current tickets

### Filter by Status
```python
status_filter = st.selectbox(..., ["All", "Pending Review", "In Progress", "Resolved"])
if status_filter != "All":
    filtered_tickets = [t for t in filtered_tickets if t['status'] == status_filter]
```
Fixed status options matching update logic

---

## 🔄 Status Update Workflow

```
User clicks "Mark In Progress":
  ↓
Button key: progress_{idx}
  ↓
Find ticket by index
  ↓
Update: tickets[index]['status'] = "In Progress"
  ↓
save_tickets(tickets) → JSON updated
  ↓
st.rerun() → Page refreshes with new status
  ↓
Display now shows: 🔄 In Progress
```

---

## 🛡️ Error Handling

### CSV Loading Errors:
```python
try:
    with open('Dataset - Dataset.csv', mode='r') as f:
        # Load routing logic
except Exception as e:
    st.error(f"Error loading CSV: {e}")
```

### File Operations:
```python
def load_tickets():
    if Path(TICKETS_FILE).exists():
        with open(TICKETS_FILE, 'r') as f:
            return json.load(f)
    return []  # Return empty list if file doesn't exist
```

---

## 📈 Scalability Considerations

### Performance:
- ROUTING_LOGIC loaded once at startup (cached)
- JSON file grows with tickets (can be archived)
- Filter operations are in-memory (fast even with hundreds of tickets)

### Limitations:
- Single JSON file → Could migrate to database for 1000+ tickets
- In-memory ticket list → Refresh required to see team updates
- No authentication → Suitable for internal use within organization

### Future Enhancements:
```
Possible additions:
├─ Database backend (PostgreSQL/MongoDB)
├─ Team member login authentication
├─ Real-time ticket notifications
├─ Automatic email alerts
├─ Ticket priority re-ranking
├─ Performance analytics
├─ Image storage/retrieval
└─ Customer follow-up tracking
```

---

## 🎯 Key Design Decisions

1. **CSV-Based Routing**: Easy to update without code changes
2. **Auto-Generated Ticket IDs**: Timestamp-based, human-readable format
3. **Team Identifiers**: Simple number-based (P01, P02) for quick reference
4. **JSON Persistence**: Simple, human-readable, easy to backup
5. **Dual-Tab Interface**: Clear separation of concerns (customer vs. team)
6. **Smart Recipient Detection**: "Technician" keyword in action field
7. **Status Tracking**: Simple states matching common workflows
8. **No Authentication**: Prototype suitable for internal tools

---

## 📝 Implementation Notes

### CSV Requirements:
- Must include all required columns
- "Action Required" field drives routing
- "Evidence" column must have team identifiers
- Labels must match AI model detection outputs

### API Integration:
- Roboflow API used for object detection
- Confidence threshold: 25% (adjustable)
- Supports image formats: JPG, PNG
- Supports video formats: MP4, MOV

### Streamlit Features Used:
- `st.tabs()` - Multi-tab interface
- `st.file_uploader()` - File input
- `st.selectbox()` - Dropdown filters
- `st.metric()` - Key information display
- `st.expander()` - Collapsible ticket details
- `st.container(border=True)` - Visual separation
- `st.rerun()` - Refresh page after updates

