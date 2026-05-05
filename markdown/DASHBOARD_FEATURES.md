# REcharge Smart Diagnostic Hub - Enhanced Features Guide

## 🎯 Overview

The enhanced REcharge dashboard now includes intelligent routing of diagnostic issues to either customers or the after-sales team based on the severity and nature of the fault.

---

## 📋 Key Features

### 1. **Intelligent Issue Routing**
The system automatically analyzes detected faults and routes them to the appropriate recipient:

- **👤 Customer-Directed Issues**: Simple troubleshooting steps that customers can resolve themselves
- **🔧 Technician-Directed Issues**: Complex issues requiring after-sales team expertise

### 2. **Two-Tab Interface**

#### **Tab 1: 🔍 Diagnostic Analysis**
- Upload images/videos of your EV charger
- AI automatically detects and analyzes faults
- Displays device information (Brand, Model, Serial Number)
- Shows observation results with severity and category

**For Customer Issues:**
- Clear, step-by-step troubleshooting instructions
- Specific actions to take
- Easy-to-understand guidance

**For After-Sales Issues:**
- Automatic ticket generation
- Unique ticket ID (AST-[timestamp])
- Team assignment with identifier (P01, P02, etc.)
- Status tracking

#### **Tab 2: 📋 After-Sales Team Dashboard**
- View all escalated tickets
- Filter by Team ID or Status
- Track ticket progress:
  - 🟡 Pending Review
  - 🔄 In Progress
  - ✅ Resolved
- Update ticket status
- Delete resolved tickets

---

## 🔄 Routing Logic

### Customer Detection
Issues routed to **customers** when the CSV "Action Required" field contains **user-friendly terms** like:
- "User: ..."
- "Contact TNB..."
- "Ensure..."
- "Turn off..."

### After-Sales Team Detection
Issues routed to **after-sales team** when "Action Required" contains **technical terms** like:
- "Technician: ..."
- "Replace damaged components..."
- "Fix overload issue..."
- "Repair internal circuit..."

---

## 📊 Ticket Information

Each routed ticket contains:

```
Ticket Details:
├── Ticket ID (Auto-generated: AST-YYYYMMDDHHMMSS)
├── Team ID (P01, P02, P03, etc. - from CSV Evidence column)
├── Status (Pending Review / In Progress / Resolved)
├── Timestamp (Creation time)
├── Equipment Details
│   ├── Brand/Model
│   ├── Serial Number
│   └── File Name
├── Fault Analysis
│   ├── Observation (detected fault label)
│   ├── Severity (Critical/High/Medium/Low)
│   ├── Category (Electrical, Hardware, etc.)
│   ├── Troubleshooting Steps
│   └── Required Actions
```

---

## 💾 Data Persistence

Routed tickets are automatically saved to `routing_tickets.json` file in the application directory with the following structure:

```json
[
  {
    "ticket_id": "AST-20260505021234",
    "timestamp": "2026-05-05T02:12:34.567890",
    "team_id": "P02",
    "file_name": "charger_image.jpg",
    "brand": "Proton eMAS",
    "model": "7kW",
    "serial": "SN12345678",
    "fault_label": "burnt_mark_issue",
    "observation": "Burnt Mark Issue",
    "troubleshooting_steps": "Turn off power immediately. Check inside for melted or discolored parts.",
    "action_required": "Technician: Replace damaged components; Rewire if necessary",
    "status": "Pending Review"
  }
]
```

---

## 🎨 Display Sections

### 👤 Actions for You (Customer)
- Shows with customer-friendly styling
- Includes severity badge (Critical/High/Medium/Low)
- Issue category label
- Clear troubleshooting steps
- Specific actions to take

### 🔧 Escalated to After-Sales Team
- Shows ticket information prominently
- Displays auto-generated Ticket ID
- Shows assigned Team ID for internal routing
- Status indicator (Pending Review)
- Technical details for technician review
- Code blocks for detailed information

---

## 🛠️ Team Actions (After-Sales Tab)

### Available Actions:
1. **🔄 Mark In Progress** - Update ticket status to "In Progress"
2. **✅ Mark Resolved** - Update ticket status to "Resolved"
3. **🗑️ Delete Ticket** - Remove processed/archived tickets

### Filtering Options:
- **Filter by Team ID** - View tickets assigned to specific teams
- **Filter by Status** - View tickets by their current status

---

## 📈 Workflow Example

### Scenario 1: Customer-Solvable Issue
1. Customer uploads charger image
2. AI detects "Isolator_ON/OFF" fault
3. CSV indicates "User: Flip switch to ON"
4. Dashboard displays:
   - **For Customer**: Clear instruction to flip the switch
   - ✅ No ticket created

### Scenario 2: Technician-Required Issue
1. Customer uploads charger image
2. AI detects "Burnt_mark_issue" fault
3. CSV indicates "Technician: Replace damaged components"
4. Dashboard displays:
   - **Ticket Created**: AST-20260505021234
   - **Assigned to**: Team P02
   - For customer: Message explaining escalation
   - For technician: Full technical details available in After-Sales Tickets tab

---

## 📝 CSV Data Requirements

Ensure your `Dataset - Dataset.csv` includes these columns:

| Column | Purpose | Example |
|--------|---------|---------|
| Fault ID | Unique identifier | 7kW-01 |
| Detection Label | AI detection label | Charger_unable_to_power_up |
| Issue Category | Categorization | Electrical & Utility |
| Severity | Priority level | Critical |
| Troubleshooting Steps & Parameters | Steps to diagnose | Check voltage at charger... |
| Action Required | Recipient determination | Technician: Rectify faulty component |
| Evidence | Team identifier | P01 |

---

## 🚀 Getting Started

1. **Start the application:**
   ```bash
   python -m streamlit run app.py
   ```

2. **Access the dashboard:**
   - Open `http://localhost:8501` in your browser

3. **Upload evidence:**
   - Use the **Diagnostic Analysis** tab
   - Upload JPG, PNG, MP4, or MOV files

4. **Check routed issues:**
   - Go to **After-Sales Tickets** tab
   - View all escalated tickets
   - Update ticket status as needed

---

## 🔐 Data Files

- **routing_tickets.json** - Automatically created and updated
  - Stores all routed ticket information
  - Persists across sessions
  - Can be backed up for archival

---

## ✨ Benefits

✅ **Automated Routing** - No manual ticket assignment needed  
✅ **Clear Communication** - Customers and technicians see appropriate information  
✅ **Team Tracking** - After-sales can monitor ticket status  
✅ **Data Persistence** - All tickets saved for future reference  
✅ **Quick Resolution** - Simple issues resolved by customers without waiting  
✅ **Efficient Escalation** - Complex issues routed to correct team  

---

## 📞 Support

For issues or questions about the system, refer to the CSV data and ensure:
1. Detection labels match AI model outputs
2. "Action Required" field clearly indicates recipient
3. Team IDs are properly set in the Evidence column
