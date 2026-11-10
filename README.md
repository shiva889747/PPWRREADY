# PPWRREADY — Packaging Data & Digital Readiness Assessment

A Flask-based prototype for assessing the current state of packaging master data, identifying data-quality gaps, tracking remediation and preparing structured information for PPWR-related compliance reporting activities.

## Core capabilities
- Executive readiness dashboard
- Packaging master-data register
- Add, edit and delete packaging records
- Record-level readiness checks and scoring
- Gap analysis and remediation queue
- Five-dimension digital-readiness assessment
- Supplier readiness analytics
- What-if readiness simulator
- Remediation action tracker with owner, due date, priority and status
- Assessment snapshots/history
- Audit trail for create/update/delete/import events
- CSV import with validation and preview
- CSV and JSON export
- Data dictionary / governance definitions
- Printable management compliance-readiness report
- JSON summary API (`/api/summary`)

## Technology
- Python 3.11+ recommended
- Flask
- SQLite
- HTML + CSS + vanilla JavaScript
- No external frontend libraries or internet connection required after dependencies are installed

## Run on Windows
```cmd
cd C:\src\ppwr_college_project
.venv\Scripts\activate
python app.py
```
Then open `http://127.0.0.1:5000`.

If the virtual environment has not yet been created:
```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Recommended faculty demo
1. Dashboard — explain readiness KPIs and data gaps.
2. Packaging Register — open a low-readiness record.
3. Record Assessment — show PASS/GAP checks.
4. Edit that record — add missing evidence and save.
5. Return to Dashboard — show that the readiness value changes.
6. Gap Analysis — show the updated remediation need.
7. What-if Simulator — demonstrate how closing selected gaps could improve the portfolio score without changing real data.
8. Remediation Actions — create an owner/due-date action.
9. Supplier Analytics — compare suppliers by evidence coverage.
10. Assessment History — save a snapshot before/after changes.
11. Audit Trail — show that changes are traceable.
12. Compliance Report — print/save a management summary.
13. Export CSV/JSON — demonstrate reporting interoperability.

## Important scope statement
The sample dataset is simulated. The readiness scoring and thresholds are an academic/internal assessment methodology designed to demonstrate data governance and digital readiness. They do not constitute an official PPWR legal-compliance certification.
