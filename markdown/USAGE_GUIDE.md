# REcharge Dashboard - Usage Guide & Examples

## 🚀 Quick Start

### Step 1: Start the Application
```bash
cd c:\Users\limyi\OneDrive\Documents\GitHub\rexcharge2026
python -m streamlit run app.py
```

### Step 2: Open in Browser
```
http://localhost:8501
```

### Step 3: You'll see the dashboard with 2 tabs:
- 🔍 **Diagnostic Analysis** (active by default)
- 📋 **After-Sales Tickets**

---

## 📋 Tab 1: Diagnostic Analysis Workflow

### A. Upload Evidence
1. Click **"Choose File"** or drag & drop
2. Select JPG, PNG, MP4, or MOV file
3. Supported files: charger images, technical photos, videos

### B. System Analyzes
1. AI detects:
   - **Brand/Model** (from visible logo/label)
   - **Serial Number** (from label text)
   - **Faults** (burnt marks, LED indicators, physical damage)

2. CSV lookups determine recipient:
   - Extract troubleshooting steps
   - Extract action required
   - Determine if customer or technician issue

### C. Results Display

#### Example 1: Customer-Solvable Issue
```
User uploads image of 7kW charger with:
- Brand: Proton eMAS
- Model: 7kW
- Serial: SN12345678
- Detected Fault: Isolator_ON/OFF

CSV Lookup (from row with Detection Label = "Isolator_ON/OFF"):
- Action Required: "User/Technician: Flip switch to ON; Replace isolator if faulty"
- Contains "Technician"? YES → But contains "User" as primary
- Decision: CUSTOMER (because no pure "Technician" directive)

Display Output:
┌─────────────────────────────────────────────────┐
│ 👤 Actions for You (Customer)                   │
├─────────────────────────────────────────────────┤
│ 🔍 Observation: Isolator On/Off                │
│ Severity: `Low` | Category: `Operational`      │
│                                                 │
│ 📝 Troubleshooting Steps:                      │
│ Check the isolator switch on the side          │
│ of the unit.                                   │
│                                                 │
│ ✅ What You Should Do:                         │
│ User/Technician: Flip switch to ON;            │
│ Replace isolator if faulty                     │
└─────────────────────────────────────────────────┘

✅ No ticket created
```

#### Example 2: Technician-Required Issue
```
User uploads image of charger showing burnt areas:
- Brand: Proton eMAS
- Model: 7kW
- Serial: SN87654321
- Detected Fault: Burnt_mark_issue

CSV Lookup (from row with Detection Label = "Burnt_mark_issue"):
- Action Required: "Technician: Replace damaged components; Rewire if necessary"
- Contains "Technician"? YES → TECHNICIAN
- Evidence: P02 (Team identifier)
- Decision: AFTER-SALES TEAM

Display Output:
┌──────────────────────────────────────────────────────┐
│ 🔧 Escalated to After-Sales Team                    │
├──────────────────────────────────────────────────────┤
│ 🚨 Observation: Burnt Mark Issue                    │
│ Severity: `Critical` | Category: `Hardware Failure`│
│                                                      │
│ Ticket ID        │ AST-20260505021234               │
│ Assigned Team    │ P02                              │
│ Status           │ 🟡 Pending Review                │
│                                                      │
│ 📋 Troubleshooting Steps (for technician):         │
│ ┌────────────────────────────────────────────────┐ │
│ │ Turn off power immediately. Check inside for  │ │
│ │ melted or discolored parts.                   │ │
│ └────────────────────────────────────────────────┘ │
│                                                      │
│ ⚙️ Required Actions:                               │
│ ┌────────────────────────────────────────────────┐ │
│ │ Technician: Replace damaged components;       │ │
│ │ Rewire if necessary                           │ │
│ └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘

✅ Ticket Created and Routed to Team P02
✅ Message: "1 ticket(s) routed to After-Sales Team"
```

---

## 📋 Tab 2: After-Sales Ticket Management

### Access the Dashboard
1. Click the **"📋 After-Sales Tickets"** tab
2. View all escalated tickets from previous analyses

### Dashboard Layout

#### Ticket Summary
```
Total Tickets: 5

Filter by Team ID: [All ▼]
Filter by Status: [All ▼]
```

#### Individual Ticket View
Each ticket appears as an expandable section:

```
🎫 AST-20260505021234 | Burnt Mark Issue | Team: P02
```

Click to expand and see full details:

```
┌─────────────────────────────────────────────────────────────┐
│ Ticket ID          │ AST-20260505021234                    │
│ Team ID            │ P02                                   │
│ Status             │ 🟡 Pending Review                     │
│ Created            │ 2026-05-05                            │
├─────────────────────────────────────────────────────────────┤
│ 📦 Equipment Details:                                       │
│ Brand/Model: Proton eMAS / 7kW                             │
│ Serial: SN87654321                                         │
│ File: charger_damage.jpg                                   │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Fault Analysis:                                          │
│ Observation: Burnt Mark Issue                              │
│                                                             │
│ Troubleshooting Steps (for technician):                    │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Turn off power immediately. Check inside for melted  │ │
│ │ or discolored parts.                                 │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                             │
│ Required Actions:                                           │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Technician: Replace damaged components; Rewire if   │ │
│ │ necessary                                            │ │
│ └───────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 🛠️ Team Actions:                                           │
│ [🔄 Mark In Progress] [✅ Mark Resolved] [🗑️ Delete]     │
└─────────────────────────────────────────────────────────────┘
```

### Managing Tickets

#### Update Status - Mark In Progress
```
When technician starts working on ticket:
1. Click [🔄 Mark In Progress] button
2. Status changes to: 🔄 In Progress
3. Dashboard refreshes automatically
```

#### Update Status - Mark Resolved
```
When issue is resolved:
1. Click [✅ Mark Resolved] button
2. Status changes to: ✅ Resolved
3. Dashboard refreshes automatically
```

#### Delete Ticket
```
To remove processed/archived tickets:
1. Click [🗑️ Delete Ticket] button
2. Ticket is removed from dashboard
3. Deleted from routing_tickets.json
```

### Filtering Tickets

#### Filter by Team ID
```
Scenario: Multiple teams (P01, P02, P03, etc.)

Default: "All" - shows all tickets
Options auto-populate from current tickets

Select "P02": Shows only tickets for Team P02
Select "P01": Shows only tickets for Team P01
```

#### Filter by Status
```
Options:
- All: All tickets regardless of status
- Pending Review: 🟡 Just routed, not started
- In Progress: 🔄 Currently being worked on
- Resolved: ✅ Fixed/completed

Workflow example:
1. New ticket arrives → Status: Pending Review
2. Technician starts → Change to: In Progress
3. Technician completes → Change to: Resolved
4. Can delete resolved tickets to clean dashboard
```

---

## 📊 Real-World Examples

### Example Workflow 1: Simple Customer Issue

**Scenario**: Customer can't connect to their 7kW charger via Bluetooth

```
Step 1: Upload Evidence
┌──────────────────────┐
│ Screenshot showing   │
│ Bluetooth error in   │
│ e.BOX app            │
└──────────────────────┘
        ↓
Step 2: AI Detection
- Detected: Bluetooth_connection_failure
- Brand: Proton eMAS
- Model: 7kW
- Serial: SN-BT-001
        ↓
Step 3: Routing Logic
- CSV Row: Bluetooth_connection_failure
- Action Required: "User: Grant location permissions; Try with another phone"
- Contains "Technician"? NO
- Decision: CUSTOMER
        ↓
Step 4: Display to Customer
╔════════════════════════════════════════╗
║ 👤 Actions for You (Customer)          ║
╠════════════════════════════════════════╣
║ 🔍 Observation: Bluetooth Connection   ║
║                            Failure     ║
║ Severity: `Low`                        ║
║ Category: `Connectivity`               ║
║                                        ║
║ 📝 Troubleshooting Steps:              ║
║ Keep phone within 1m. 'Forget This     ║
║ Device' in Bluetooth settings and      ║
║ reconnect.                             ║
║                                        ║
║ ✅ What You Should Do:                 ║
║ User: Grant location permissions;      ║
║ Try with another phone                 ║
╚════════════════════════════════════════╝

Result: ✅ Customer can self-resolve
```

### Example Workflow 2: Technician-Assigned Issue

**Scenario**: 22kW charger won't output voltage

```
Step 1: Upload Evidence
┌──────────────────────┐
│ Photo of charger     │
│ connector showing    │
│ no LED indicators    │
└──────────────────────┘
        ↓
Step 2: AI Detection
- Detected: EV_Connector_no_output
- Brand: Proton eMAS
- Model: 22kW
- Serial: SN-22KW-042
        ↓
Step 3: Routing Logic
- CSV Row: EV_Connector_no_output
- Action Required: "User: Correct Connection Mode setting; Save and restart +1"
- Contains "Technician"? NO
- Decision: CUSTOMER
        ↓
Step 4: Display to Customer
╔════════════════════════════════════════╗
║ 👤 Actions for You (Customer)          ║
╠════════════════════════════════════════╣
║ 🔍 Observation: EV Connector No        ║
║                            Output      ║
║ Severity: `Medium`                     ║
║ Category: `App & Software`             ║
║                                        ║
║ 📝 Troubleshooting Steps:              ║
║ Check terminal voltage. Verify         ║
║ Connection Mode in e.BOX App.          ║
║                                        ║
║ ✅ What You Should Do:                 ║
║ User: Correct Connection Mode          ║
║ setting; Save and restart +1           ║
╚════════════════════════════════════════╝

Result: ✅ Customer tries app settings first
```

### Example Workflow 3: Escalated to After-Sales

**Scenario**: Multiple components appear damaged

```
Step 1: Upload Evidence
┌──────────────────────┐
│ Photo showing:       │
│ - Burnt marks        │
│ - Melted connectors  │
│ - Discolored parts   │
└──────────────────────┘
        ↓
Step 2: AI Detection
- Detected: Burnt_mark_issue
- Brand: Proton eMAS
- Model: 7kW
- Serial: SN-DMG-999
        ↓
Step 3: Routing Logic
- CSV Row: Burnt_mark_issue
- Action Required: "Technician: Replace damaged components; Rewire if necessary"
- Contains "Technician"? YES ✓
- Evidence (Team): P02
- Decision: AFTER-SALES TEAM
        ↓
Step 4: Create Ticket
Generated Ticket ID: AST-20260505021500

Ticket Fields:
{
  "ticket_id": "AST-20260505021500",
  "timestamp": "2026-05-05T02:15:00",
  "team_id": "P02",
  "file_name": "damaged_charger.jpg",
  "brand": "Proton eMAS",
  "model": "7kW",
  "serial": "SN-DMG-999",
  "fault_label": "burnt_mark_issue",
  "observation": "Burnt Mark Issue",
  "troubleshooting_steps": "Turn off power immediately...",
  "action_required": "Technician: Replace damaged...",
  "status": "Pending Review"
}
        ↓
Step 5: Display to After-Sales Team
In Dashboard Tab 2 → After-Sales Tickets:

🎫 AST-20260505021500 | Burnt Mark Issue | Team: P02

[Expand to see details]
        ↓
Step 6: Team Actions
Team P02 technician:
1. Receives notification (view in tab 2)
2. Reviews ticket details
3. Clicks [🔄 Mark In Progress]
4. Works on device repair
5. Upon completion: [✅ Mark Resolved]
6. Can delete after archiving: [🗑️ Delete]

Result: ✅ Damage assessed and scheduled for repair
```

---

## 🎯 Best Practices

### For Dashboard Users (Customers)

1. **Take clear photos**:
   - Good lighting
   - Show error codes/indicators
   - Include serial number label

2. **Upload one issue at a time**:
   - Helps AI detection accuracy
   - Clearer troubleshooting steps
   - Easier to track

3. **Follow displayed instructions**:
   - Read all troubleshooting steps
   - Execute actions in order
   - Document any error codes

### For After-Sales Team

1. **Check tickets regularly**:
   - Use Tab 2 dashboard
   - Filter by team to see your assignments
   - Update status frequently

2. **Update ticket status**:
   - Mark "In Progress" when starting
   - Mark "Resolved" when completed
   - Delete after archiving

3. **Refer to ticket details**:
   - Use troubleshooting steps as guide
   - Check equipment serial number
   - Note original file name for reference

---

## 💾 Data File Management

### Viewing routing_tickets.json
```
Location: c:\Users\limyi\OneDrive\Documents\GitHub\rexcharge2026\

Content: JSON array of ticket objects
Size: Grows with each routed ticket (~2KB per ticket)

Backup: Regular copy to archives folder recommended
```

### Archiving Old Tickets
```
1. Open routing_tickets.json
2. Find tickets with "Resolved" status
3. Copy resolved tickets to backup file
4. Delete from routing_tickets.json
5. Dashboard auto-refreshes
```

---

## 🐛 Troubleshooting

### Issue: No faults detected
```
Possible causes:
1. Image quality too low
2. Confidence threshold too high
3. Fault not in AI training data

Solution:
- Try clearer photo
- Check CSV has detection labels
- Upload to Roboflow to verify
```

### Issue: Ticket not appearing in Tab 2
```
Possible causes:
1. Page not refreshed
2. JSON file corrupted
3. Wrong status filter applied

Solution:
- Refresh browser
- Check routing_tickets.json exists
- Check filter settings ("All" by default)
```

### Issue: Status changes revert
```
Possible causes:
1. Page crashed during save
2. File permission issues
3. JSON file lock

Solution:
- Try again
- Check file permissions
- Restart Streamlit app
```

---

## 📞 Support Reference

| Issue | Solution |
|-------|----------|
| App won't start | Check Python 3.13 installed, run `pip install -r requirements.txt` |
| API errors | Verify API_KEY in app.py, check internet connection |
| CSV errors | Verify column names match exactly |
| File upload fails | Check file size < 200MB, format is supported |
| Tickets disappear | Check routing_tickets.json not deleted |
| Performance slow | Archive old resolved tickets |

