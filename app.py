from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
import sqlite3, csv, io, os, json
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'ppwr.db')

app = Flask(__name__)
app.secret_key = 'ppwr-readiness-demo-key'

REQUIRED_FIELDS = [
    ('material', 'Material identified'),
    ('weight_g', 'Packaging weight available'),
    ('recycled_content_pct', 'Recycled content recorded'),
    ('recyclable', 'Recyclability status recorded'),
    ('supplier_evidence', 'Supplier evidence available'),
    ('label_ready', 'Labelling readiness assessed'),
    ('data_source', 'Data source traceable'),
    ('last_verified', 'Record verification date available'),
]

DATA_DICTIONARY = [
    ('sku','SKU','Unique product / packaging identifier','Required'),
    ('product_name','Product name','Commercial product name','Required'),
    ('packaging_level','Packaging level','Primary, Secondary or Transport','Recommended'),
    ('packaging_type','Packaging type','Bottle, carton, pouch, film, etc.','Recommended'),
    ('material','Material','Main packaging material','Readiness check'),
    ('weight_g','Weight (g)','Packaging component weight in grams','Readiness check'),
    ('recycled_content_pct','Recycled content (%)','Percentage of recycled material','Readiness check'),
    ('recyclable','Recyclability status','Yes / No / Unknown','Readiness check'),
    ('supplier','Supplier','Packaging supplier / converter','Recommended'),
    ('supplier_evidence','Supplier evidence','Whether supporting supplier evidence is available','Readiness check'),
    ('label_ready','Labelling readiness','Whether labelling readiness has been assessed','Readiness check'),
    ('data_source','Data source','System or repository where data originates','Readiness check'),
    ('market','Market','Target market / region','Recommended'),
    ('last_verified','Last verified','Most recent verification date','Readiness check'),
    ('notes','Notes','Supporting comments or remediation notes','Optional'),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS packaging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            product_name TEXT NOT NULL,
            packaging_level TEXT,
            packaging_type TEXT,
            material TEXT,
            weight_g REAL,
            recycled_content_pct REAL,
            recyclable TEXT,
            supplier TEXT,
            supplier_evidence TEXT,
            label_ready TEXT,
            data_source TEXT,
            market TEXT,
            last_verified TEXT,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TEXT NOT NULL,
            action TEXT NOT NULL,
            record_id INTEGER,
            sku TEXT,
            detail TEXT
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_time TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            average_score INTEGER NOT NULL,
            high_count INTEGER NOT NULL,
            medium_count INTEGER NOT NULL,
            low_count INTEGER NOT NULL,
            open_gap_count INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS remediation_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            sku TEXT,
            action_text TEXT NOT NULL,
            owner TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            created_at TEXT NOT NULL
        );
    ''')
    count = conn.execute('SELECT COUNT(*) FROM packaging').fetchone()[0]
    if count == 0:
        rows = [
            ('SKU-1001','Orange Juice 1L','Primary','Bottle','PET',35,30,'Yes','EcoPack GmbH','Yes','Yes','ERP + Supplier Declaration','EU','2026-08-20','Good evidence coverage.'),
            ('SKU-1002','Sparkling Water 500ml','Primary','Bottle','PET',22,25,'Yes','ClearBottle Ltd','Yes','No','ERP','EU','2026-07-18','Label mapping still pending.'),
            ('SKU-1003','Breakfast Cereal 500g','Primary','Carton','Paperboard',48,0,'Yes','FiberPack BV','No','Yes','Spreadsheet','EU','2026-06-30','Supplier recyclability certificate missing.'),
            ('SKU-1004','Tomato Sauce 350g','Primary','Jar','Glass',210,0,'Yes','GlassWorks SA','Yes','Yes','PLM','EU','2026-08-05','Complete baseline record.'),
            ('SKU-1005','Shampoo 250ml','Primary','Bottle','HDPE',28,18,'Yes','PolyForm SpA','No','No','Email + Spreadsheet','EU','2026-05-11','Supplier evidence and labelling need action.'),
            ('SKU-1006','Coffee Beans 1kg','Primary','Pouch','Multi-layer Plastic',32,None,'Unknown','FlexiPack SRL','No','No','Spreadsheet','EU',None,'Composition and recyclability evidence incomplete.'),
            ('SKU-1007','Chocolate Gift Box','Secondary','Box','Paperboard',85,60,'Yes','FiberPack BV','Yes','Yes','PLM','EU','2026-08-25','High readiness.'),
            ('SKU-1008','Laundry Capsules 30ct','Primary','Tub','PP',64,20,'Yes','PackTech NV','Yes','No','ERP + Supplier Portal','EU','2026-08-01','Harmonised label readiness pending.'),
            ('SKU-1009','Frozen Vegetables 750g','Primary','Film','LDPE',14,None,'Unknown','FlexiPack SRL','No','No','Spreadsheet','EU','2026-03-15','Major data gap.'),
            ('SKU-1010','Olive Oil 750ml','Primary','Bottle','Glass',390,0,'Yes','GlassWorks SA','Yes','Yes','PLM + Supplier Declaration','EU','2026-08-28','Complete baseline record.'),
            ('SKU-1011','Protein Bar 60g','Primary','Wrapper','Plastic laminate',4,None,'No','WrapCo','No','No','Email','EU',None,'Material detail and evidence require remediation.'),
            ('SKU-1012','Hand Soap 500ml','Primary','Bottle','PET',31,35,'Yes','EcoPack GmbH','Yes','Yes','ERP + Supplier Declaration','EU','2026-09-01','Ready for reporting prototype.'),
        ]
        conn.executemany('''INSERT INTO packaging
        (sku,product_name,packaging_level,packaging_type,material,weight_g,recycled_content_pct,recyclable,supplier,supplier_evidence,label_ready,data_source,market,last_verified,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', rows)
    conn.commit(); conn.close()


def log_event(action, record_id=None, sku=None, detail=''):
    conn = get_db()
    conn.execute('INSERT INTO audit_log(event_time,action,record_id,sku,detail) VALUES (?,?,?,?,?)',
                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), action, record_id, sku, detail))
    conn.commit(); conn.close()


def score_record(row):
    checks = {}
    for field, label in REQUIRED_FIELDS:
        value = row[field]
        ok = value is not None and str(value).strip() != '' and str(value).strip().lower() not in ('unknown','n/a')
        if field in ('supplier_evidence', 'label_ready'):
            ok = str(value).strip().lower() == 'yes'
        checks[label] = ok
    score = round(sum(checks.values()) / len(checks) * 100)
    status = 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low'
    return score, status, checks


def dashboard_metrics(rows):
    scored = [score_record(r) for r in rows]
    avg = round(sum(s[0] for s in scored) / len(scored)) if scored else 0
    high = sum(1 for s in scored if s[1] == 'High')
    medium = sum(1 for s in scored if s[1] == 'Medium')
    low = sum(1 for s in scored if s[1] == 'Low')
    gaps = {label: 0 for _, label in REQUIRED_FIELDS}
    for _, _, checks in scored:
        for label, ok in checks.items():
            if not ok: gaps[label] += 1
    return avg, high, medium, low, gaps


def parse_number(v):
    if v is None or str(v).strip() == '': return None
    try: return float(v)
    except ValueError: return None


def form_payload(f):
    return (
        (f.get('sku') or '').strip(), (f.get('product_name') or '').strip(), f.get('packaging_level') or None,
        f.get('packaging_type') or None, f.get('material') or None, parse_number(f.get('weight_g')),
        parse_number(f.get('recycled_content_pct')), f.get('recyclable') or None, f.get('supplier') or None,
        f.get('supplier_evidence') or None, f.get('label_ready') or None, f.get('data_source') or None,
        f.get('market') or None, f.get('last_verified') or None, f.get('notes') or None
    )


@app.route('/')
def dashboard():
    conn = get_db(); rows = conn.execute('SELECT * FROM packaging ORDER BY id').fetchall()
    open_actions = conn.execute("SELECT COUNT(*) FROM remediation_actions WHERE status!='Closed'").fetchone()[0]
    last_snapshot = conn.execute('SELECT * FROM snapshots ORDER BY id DESC LIMIT 1').fetchone(); conn.close()
    avg, high, medium, low, gaps = dashboard_metrics(rows)
    material_counts = {}
    for r in rows: material_counts[r['material'] or 'Unknown'] = material_counts.get(r['material'] or 'Unknown', 0) + 1
    evidence_ready = round(sum(1 for r in rows if r['supplier_evidence'] == 'Yes') / len(rows) * 100) if rows else 0
    label_ready = round(sum(1 for r in rows if r['label_ready'] == 'Yes') / len(rows) * 100) if rows else 0
    verified = round(sum(1 for r in rows if r['last_verified']) / len(rows) * 100) if rows else 0
    critical_gaps = sum(1 for count in gaps.values() if count > 0)
    material_max = max(material_counts.values()) if material_counts else 1
    recent = list(reversed(rows[-5:]))
    return render_template('dashboard.html', rows=rows, avg=avg, high=high, medium=medium, low=low, gaps=gaps,
        materials=material_counts, material_max=material_max, evidence_ready=evidence_ready, label_ready=label_ready,
        verified=verified, critical_gaps=critical_gaps, recent=recent, refreshed=datetime.now().strftime('%d %b %Y'),
        open_actions=open_actions, last_snapshot=last_snapshot)

@app.route('/packaging')
def packaging():
    conn = get_db(); rows = conn.execute('SELECT * FROM packaging ORDER BY id DESC').fetchall(); conn.close()
    enriched=[(r,*score_record(r)[:2]) for r in rows]
    return render_template('packaging.html', rows=enriched)

@app.route('/add', methods=['GET','POST'])
def add_record():
    if request.method == 'POST':
        payload=form_payload(request.form)
        if not payload[0] or not payload[1]: flash('SKU and product name are required.'); return render_template('add.html')
        conn=get_db(); cur=conn.execute('''INSERT INTO packaging (sku,product_name,packaging_level,packaging_type,material,weight_g,recycled_content_pct,recyclable,supplier,supplier_evidence,label_ready,data_source,market,last_verified,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', payload); conn.commit(); conn.close()
        log_event('Created record', cur.lastrowid, payload[0], payload[1]); flash('Packaging record added successfully.'); return redirect(url_for('record',record_id=cur.lastrowid))
    return render_template('add.html')

@app.route('/record/<int:record_id>')
def record(record_id):
    conn=get_db(); row=conn.execute('SELECT * FROM packaging WHERE id=?',(record_id,)).fetchone(); actions=conn.execute('SELECT * FROM remediation_actions WHERE record_id=? ORDER BY id DESC',(record_id,)).fetchall(); conn.close()
    if not row: return ('Not found',404)
    score,status,checks=score_record(row)
    return render_template('record.html', row=row, score=score, status=status, checks=checks, actions=actions)

@app.route('/record/<int:record_id>/edit', methods=['GET','POST'])
def edit_record(record_id):
    conn=get_db(); row=conn.execute('SELECT * FROM packaging WHERE id=?',(record_id,)).fetchone()
    if not row: conn.close(); return ('Not found',404)
    if request.method=='POST':
        payload=form_payload(request.form)
        conn.execute('''UPDATE packaging SET sku=?,product_name=?,packaging_level=?,packaging_type=?,material=?,weight_g=?,recycled_content_pct=?,recyclable=?,supplier=?,supplier_evidence=?,label_ready=?,data_source=?,market=?,last_verified=?,notes=? WHERE id=?''', payload+(record_id,)); conn.commit(); conn.close()
        log_event('Updated record', record_id, payload[0], payload[1]); flash('Record updated successfully.'); return redirect(url_for('record',record_id=record_id))
    conn.close(); return render_template('edit.html', row=row)

@app.route('/record/<int:record_id>/delete', methods=['POST'])
def delete_record(record_id):
    conn=get_db(); row=conn.execute('SELECT * FROM packaging WHERE id=?',(record_id,)).fetchone()
    if row:
        conn.execute('DELETE FROM packaging WHERE id=?',(record_id,)); conn.commit(); conn.close(); log_event('Deleted record', record_id, row['sku'], row['product_name']); flash('Record deleted.')
    else: conn.close()
    return redirect(url_for('packaging'))

@app.route('/gaps')
def gaps():
    conn=get_db(); rows=conn.execute('SELECT * FROM packaging ORDER BY id').fetchall(); conn.close()
    _,_,_,_,gap_counts=dashboard_metrics(rows); issue_rows=[]
    for r in rows:
        score,status,checks=score_record(r); missing=[k for k,v in checks.items() if not v]
        if missing: issue_rows.append((r,score,status,missing))
    return render_template('gaps.html', gaps=gap_counts, rows=issue_rows)

@app.route('/readiness')
def readiness():
    conn=get_db(); rows=conn.execute('SELECT * FROM packaging ORDER BY id').fetchall(); conn.close()
    avg,high,medium,low,gaps=dashboard_metrics(rows)
    dimensions = {
        'Data completeness': max(0, 100-round(sum(gaps.values())/(len(rows)*len(REQUIRED_FIELDS))*100)) if rows else 0,
        'Evidence availability': round(sum(1 for r in rows if r['supplier_evidence']=='Yes')/len(rows)*100) if rows else 0,
        'Labelling readiness': round(sum(1 for r in rows if r['label_ready']=='Yes')/len(rows)*100) if rows else 0,
        'Digital traceability': round(sum(1 for r in rows if r['data_source'] and r['data_source'] not in ('Email','Spreadsheet'))/len(rows)*100) if rows else 0,
        'Verification freshness': round(sum(1 for r in rows if r['last_verified'])/len(rows)*100) if rows else 0,
    }
    overall=round(sum(dimensions.values())/len(dimensions))
    return render_template('readiness.html', dimensions=dimensions, overall=overall, avg=avg)

@app.route('/suppliers')
def suppliers():
    conn=get_db(); rows=conn.execute('SELECT * FROM packaging ORDER BY supplier').fetchall(); conn.close()
    groups=defaultdict(list)
    for r in rows: groups[r['supplier'] or 'Unassigned'].append(r)
    summary=[]
    for supplier,items in groups.items():
        scores=[score_record(x)[0] for x in items]
        evidence=sum(1 for x in items if x['supplier_evidence']=='Yes')
        summary.append({'supplier':supplier,'records':len(items),'avg':round(sum(scores)/len(scores)),'evidence':round(evidence/len(items)*100),'low':sum(1 for x in items if score_record(x)[1]=='Low')})
    summary.sort(key=lambda x:(x['avg'],x['supplier']))
    return render_template('suppliers.html', suppliers=summary)

@app.route('/actions', methods=['GET','POST'])
def actions():
    conn=get_db()
    if request.method=='POST':
        record_id=request.form.get('record_id') or None; sku=request.form.get('sku') or None; action_text=request.form.get('action_text','').strip()
        if action_text:
            conn.execute('INSERT INTO remediation_actions(record_id,sku,action_text,owner,due_date,priority,status,created_at) VALUES (?,?,?,?,?,?,?,?)',
                         (record_id,sku,action_text,request.form.get('owner'),request.form.get('due_date'),request.form.get('priority','Medium'),'Open',datetime.now().strftime('%Y-%m-%d %H:%M:%S'))); conn.commit(); flash('Remediation action created.')
    actions=conn.execute('SELECT * FROM remediation_actions ORDER BY CASE status WHEN "Open" THEN 0 WHEN "In Progress" THEN 1 ELSE 2 END, id DESC').fetchall(); records=conn.execute('SELECT id,sku,product_name FROM packaging ORDER BY sku').fetchall(); conn.close()
    return render_template('actions.html', actions=actions, records=records)

@app.route('/action/<int:action_id>/status', methods=['POST'])
def action_status(action_id):
    status=request.form.get('status','Open'); conn=get_db(); conn.execute('UPDATE remediation_actions SET status=? WHERE id=?',(status,action_id)); conn.commit(); conn.close(); flash('Action status updated.'); return redirect(url_for('actions'))

@app.route('/simulator', methods=['GET','POST'])
def simulator():
    conn=get_db(); rows=conn.execute('SELECT * FROM packaging ORDER BY id').fetchall(); conn.close(); avg,*_=dashboard_metrics(rows)
    selected=request.form.getlist('fields') if request.method=='POST' else []
    improved=[]
    for r in rows:
        _,_,checks=score_record(r); passed=sum(checks.values())
        for field,label in REQUIRED_FIELDS:
            if field in selected and not checks[label]: passed += 1
        improved.append(round(passed/len(REQUIRED_FIELDS)*100))
    projected=round(sum(improved)/len(improved)) if improved else avg
    return render_template('simulator.html', current=avg, projected=projected, selected=selected, fields=REQUIRED_FIELDS, gain=projected-avg)

@app.route('/snapshots', methods=['GET','POST'])
def snapshots():
    conn=get_db()
    if request.method=='POST':
        rows=conn.execute('SELECT * FROM packaging').fetchall(); avg,high,medium,low,gaps=dashboard_metrics(rows)
        conn.execute('INSERT INTO snapshots(snapshot_time,record_count,average_score,high_count,medium_count,low_count,open_gap_count) VALUES (?,?,?,?,?,?,?)',
                     (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),len(rows),avg,high,medium,low,sum(gaps.values()))); conn.commit(); flash('Assessment snapshot saved.')
    snaps=conn.execute('SELECT * FROM snapshots ORDER BY id DESC').fetchall(); conn.close(); return render_template('snapshots.html', snapshots=snaps)

@app.route('/audit')
def audit():
    conn=get_db(); logs=conn.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT 200').fetchall(); conn.close(); return render_template('audit.html', logs=logs)

@app.route('/dictionary')
def dictionary():
    return render_template('dictionary.html', fields=DATA_DICTIONARY, checks=REQUIRED_FIELDS)

@app.route('/import', methods=['GET','POST'])
def import_csv():
    preview=[]; errors=[]
    if request.method=='POST':
        file=request.files.get('file')
        if not file or not file.filename.lower().endswith('.csv'):
            flash('Please choose a CSV file.'); return render_template('import.html', preview=[], errors=[])
        text=file.stream.read().decode('utf-8-sig'); reader=csv.DictReader(io.StringIO(text)); expected=[x[0] for x in DATA_DICTIONARY]
        missing=[x for x in ['sku','product_name'] if x not in (reader.fieldnames or [])]
        if missing: errors.append('Missing required column(s): '+', '.join(missing))
        else:
            parsed=[]
            for i,row in enumerate(reader,start=2):
                if not row.get('sku') or not row.get('product_name'): errors.append(f'Row {i}: SKU and product_name are required.'); continue
                parsed.append(tuple([row.get(k) or None for k in ['sku','product_name','packaging_level','packaging_type','material']] + [parse_number(row.get('weight_g')),parse_number(row.get('recycled_content_pct'))] + [row.get(k) or None for k in ['recyclable','supplier','supplier_evidence','label_ready','data_source','market','last_verified','notes']]))
            if not errors and request.form.get('confirm')=='yes':
                conn=get_db(); conn.executemany('''INSERT INTO packaging (sku,product_name,packaging_level,packaging_type,material,weight_g,recycled_content_pct,recyclable,supplier,supplier_evidence,label_ready,data_source,market,last_verified,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',parsed); conn.commit(); conn.close(); log_event('CSV import', None, None, f'{len(parsed)} records imported'); flash(f'{len(parsed)} records imported successfully.'); return redirect(url_for('packaging'))
            preview=parsed[:10]
            if not errors and request.form.get('confirm')!='yes':
                return render_template('import.html', preview=preview, errors=[], raw_count=len(parsed), csv_text=text)
    return render_template('import.html', preview=preview, errors=errors)

@app.route('/import-confirm', methods=['POST'])
def import_confirm():
    text=request.form.get('csv_text',''); reader=csv.DictReader(io.StringIO(text)); parsed=[]
    for row in reader:
        if row.get('sku') and row.get('product_name'):
            parsed.append(tuple([row.get(k) or None for k in ['sku','product_name','packaging_level','packaging_type','material']] + [parse_number(row.get('weight_g')),parse_number(row.get('recycled_content_pct'))] + [row.get(k) or None for k in ['recyclable','supplier','supplier_evidence','label_ready','data_source','market','last_verified','notes']]))
    conn=get_db(); conn.executemany('''INSERT INTO packaging (sku,product_name,packaging_level,packaging_type,material,weight_g,recycled_content_pct,recyclable,supplier,supplier_evidence,label_ready,data_source,market,last_verified,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',parsed); conn.commit(); conn.close(); log_event('CSV import',None,None,f'{len(parsed)} records imported'); flash(f'{len(parsed)} records imported successfully.'); return redirect(url_for('packaging'))

@app.route('/report')
def report():
    conn=get_db(); rows=conn.execute('SELECT * FROM packaging ORDER BY id').fetchall(); actions=conn.execute("SELECT COUNT(*) FROM remediation_actions WHERE status!='Closed'").fetchone()[0]; conn.close()
    avg,high,medium,low,gaps=dashboard_metrics(rows)
    return render_template('report.html', rows=rows, avg=avg, high=high, medium=medium, low=low, gaps=gaps, actions=actions, generated=datetime.now().strftime('%d %b %Y %H:%M'))

@app.route('/export.csv')
def export_csv():
    conn=get_db(); rows=conn.execute('SELECT * FROM packaging ORDER BY id').fetchall(); conn.close(); output=io.StringIO(); w=csv.writer(output)
    headers=list(rows[0].keys())+['readiness_score','readiness_status'] if rows else []
    w.writerow(headers)
    for r in rows: score,status,_=score_record(r); w.writerow(list(r)+[score,status])
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=ppwr_packaging_export.csv'})

@app.route('/export.json')
def export_json():
    conn=get_db(); rows=conn.execute('SELECT * FROM packaging ORDER BY id').fetchall(); conn.close(); data=[]
    for r in rows:
        item=dict(r); score,status,checks=score_record(r); item.update({'readiness_score':score,'readiness_status':status,'checks':checks}); data.append(item)
    return Response(json.dumps(data,indent=2), mimetype='application/json', headers={'Content-Disposition':'attachment; filename=ppwr_packaging_export.json'})

@app.route('/api/summary')
def api_summary():
    conn=get_db(); rows=conn.execute('SELECT * FROM packaging').fetchall(); conn.close(); avg,high,medium,low,gaps=dashboard_metrics(rows)
    return jsonify({'records':len(rows),'average_readiness':avg,'high':high,'medium':medium,'low':low,'gaps':gaps})

if __name__ == '__main__':
    init_db(); app.run(debug=True)
else:
    init_db()
