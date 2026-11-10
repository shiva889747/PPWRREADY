# Faculty Demo Guide — PPWRREADY

## 30-second opening
“PPWRREADY is a packaging-data governance and digital-readiness assessment system. It centralises packaging records, checks whether important reporting fields and evidence are available, identifies gaps, assigns remediation actions, tracks improvement over time and produces a management-ready readiness report.”

## Best live demonstration scenario
### Step 1 — Start with the Dashboard
Show the total records, average readiness, evidence coverage, labelling readiness and open data areas.

### Step 2 — Open a low-readiness record
Go to **Packaging Register** and open a record such as the protein bar or frozen vegetables example. Explain that each readiness check contributes to a transparent record-level score.

### Step 3 — Improve the record
Click **Edit record** and fill one or two missing fields, such as supplier evidence or verification date. Save the record.

### Step 4 — Prove the score is dynamic
The record score is recalculated automatically. Return to the Dashboard or Gap Analysis and show that the portfolio results update.

### Step 5 — Show governance, not just data entry
Open **Remediation Actions**, create an action such as “Obtain supplier material declaration,” assign an owner and due date, then change its status to In Progress or Closed.

### Step 6 — Show decision support
Open **What-if Simulator** and select fields such as Supplier Evidence and Labelling Readiness. Explain that the system estimates the potential portfolio score if those gaps were fully resolved, without changing stored data.

### Step 7 — Show supplier management
Open **Supplier Analytics** and compare average readiness/evidence coverage by supplier.

### Step 8 — Show traceability
Open **Audit Trail** to show that data creation, edits, deletion and CSV imports are logged.

### Step 9 — Show trend tracking
Open **Assessment History**, save a snapshot, make an improvement and later save another snapshot. This demonstrates measurable progress over time.

### Step 10 — Finish with reporting
Open **Compliance Report**, use Print / Save PDF, and show CSV/JSON exports.

## Likely faculty questions
**Why is this more than a CRUD website?**
Because it adds a readiness model, gap analytics, supplier analytics, scenario simulation, remediation workflow, snapshots and auditability on top of data capture.

**Is the readiness score an official EU score?**
No. It is an internal/project methodology used to assess data completeness and digital readiness. The application supports compliance preparation but does not issue legal certification.

**Why SQLite?**
It is portable, lightweight and ideal for a demonstrable prototype. The same application architecture could later use PostgreSQL or another enterprise database.

**Why Flask?**
Flask keeps the backend transparent and easy to explain while still supporting database operations, routing, validation, exports and reporting workflows.

**What is the value of the simulator?**
It supports prioritisation. A team can estimate which categories of remediation would have the largest effect on data readiness before committing resources.

**What is the value of snapshots?**
Snapshots turn readiness from a one-time score into a measurable improvement programme.

**What is the audit trail for?**
It provides traceability by recording important data-change events.

**How would this scale in a real company?**
Replace SQLite with an enterprise database, connect to ERP/PLM/supplier portals, add authentication/roles, document storage, APIs, workflow notifications and regulatory rule maintenance.
