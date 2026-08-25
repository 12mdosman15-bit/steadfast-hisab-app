
import os, json, sqlite3, time, requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g, session, redirect, url_for
from geo_data import BD_GEO
from geo_data_en import BD_GEO_EN

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.secret_key = os.environ.get("APP_SECRET", "change-this-in-railway")

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "data", "app.db"))
STEADFAST_BASE_URL = os.environ.get("STEADFAST_BASE_URL", "https://portal.packzy.com/api/v1")
GEO_API_BASE = os.environ.get("GEO_API_BASE", "https://bdapis.vercel.app/geo/v2.0")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(_=None):
    conn = g.pop("db", None)
    if conn:
        conn.close()

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS parcels (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      invoice TEXT UNIQUE NOT NULL,
      recipient_name TEXT NOT NULL,
      recipient_phone TEXT NOT NULL,
      alternative_phone TEXT,
      district TEXT,
      thana TEXT,
      recipient_address TEXT NOT NULL,
      cod_amount REAL NOT NULL DEFAULT 0,
      weight REAL NOT NULL DEFAULT 1,
      note TEXT,
      item_description TEXT,
      total_lot INTEGER DEFAULT 1,
      delivery_type INTEGER DEFAULT 0,
      supplier_cost REAL DEFAULT 0,
      supplier_name TEXT,
      consignment_id TEXT,
      tracking_code TEXT,
      status TEXT DEFAULT 'created',
      raw_response TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_parcels_tracking ON parcels(tracking_code);
    CREATE INDEX IF NOT EXISTS idx_parcels_status ON parcels(status);

    CREATE TABLE IF NOT EXISTS expenses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      amount REAL NOT NULL,
      note TEXT,
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS suppliers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      phone TEXT,
      address TEXT,
      paid REAL DEFAULT 0,
      due REAL DEFAULT 0,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS user_settings (
      user_id INTEGER PRIMARY KEY,
      steadfast_api_key TEXT NOT NULL DEFAULT '',
      steadfast_secret_key TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    """)
    # Migrate existing single-user tables to user ownership.
    for table in ("parcels", "expenses", "suppliers"):
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if "user_id" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
    conn.commit()

@app.before_request
def before():
    init_db()

def hash_password(password):
    salt=os.urandom(16)
    digest=__import__("hashlib").pbkdf2_hmac("sha256", password.encode(), salt, 180000)
    return salt.hex()+":"+digest.hex()

def verify_password(password, stored):
    try:
        salt_hex,digest_hex=stored.split(":",1)
        salt=bytes.fromhex(salt_hex)
        check=__import__("hashlib").pbkdf2_hmac("sha256", password.encode(), salt, 180000).hex()
        return __import__("hmac").compare_digest(check,digest_hex)
    except Exception:
        return False

def current_user():
    uid = session.get("user_id")
    if not uid: return None
    return db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

def user_credentials():
    uid = session.get("user_id")
    if not uid: return "", ""
    row = db().execute("SELECT steadfast_api_key, steadfast_secret_key FROM user_settings WHERE user_id=?", (uid,)).fetchone()
    return (row[0], row[1]) if row else ("", "")

def sf_headers():
    key, secret = user_credentials()
    return {
        "Api-Key": key,
        "Secret-Key": secret,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def sf_ready():
    key, secret = user_credentials()
    return bool(key and secret)

def sf_post(path, payload):
    if not sf_ready():
        return None, "This user has not saved a Steadfast API key and secret yet. Open Settings and save them."
    try:
        r = requests.post(STEADFAST_BASE_URL.rstrip("/") + path, headers=sf_headers(),
                          json=payload, timeout=30)
        try:
            data = r.json()
        except Exception:
            data = {"message": r.text}
        if not r.ok:
            return None, f"Steadfast API HTTP {r.status_code}: {data}"
        return data, None
    except requests.RequestException as e:
        return None, f"Steadfast connection error: {e}"

def sf_get(path):
    if not sf_ready():
        return None, "This user has not saved a Steadfast API key and secret yet. Open Settings and save them."
    try:
        r = requests.get(STEADFAST_BASE_URL.rstrip("/") + path, headers=sf_headers(), timeout=30)
        try:
            data = r.json()
        except Exception:
            data = {"message": r.text}
        if not r.ok:
            return None, f"Steadfast API HTTP {r.status_code}: {data}"
        return data, None
    except requests.RequestException as e:
        return None, f"Steadfast connection error: {e}"

def make_invoice():
    stamp = datetime.now().strftime("%y%m%d%H%M%S")
    return f"SB-{stamp}-{int(time.time()*1000)%1000:03d}"

def parse_consignment(data):
    c = (data or {}).get("consignment") or (data or {}).get("data") or {}
    cid = c.get("consignment_id") or c.get("id") or (data or {}).get("consignment_id")
    tracking = c.get("tracking_code") or c.get("trackingCode") or (data or {}).get("tracking_code")
    status = c.get("status") or (data or {}).get("status") or "created"
    return str(cid) if cid is not None else None, tracking, status

def api_login_required():
    if not session.get("user_id"):
        return jsonify(ok=False, error="Login required."), 401
    return None

@app.before_request
def require_login_for_app():
    path = request.path
    public = {"/login", "/register", "/health", "/favicon.ico"}
    if path in public or path.startswith("/static/"):
        return None
    if path.startswith("/api/locations/"):
        return None
    if not session.get("user_id"):
        if path.startswith("/api/"):
            return jsonify(ok=False, error="Login required."), 401
        return redirect(url_for("login"))

@app.get("/login")
def login():
    if session.get("user_id"): return redirect(url_for("index"))
    return render_template("index.html")

@app.get("/register")
def register_page():
    if session.get("user_id"): return redirect(url_for("index"))
    return render_template("index.html")

@app.post("/api/auth/register")
def register():
    b=request.get_json(force=True) or {}
    username=str(b.get("username") or "").strip().lower()
    password=str(b.get("password") or "")
    if len(username)<3 or len(password)<6:
        return jsonify(ok=False,error="Username must be 3+ characters and password 6+ characters."),400
    try:
        now=datetime.now().isoformat(timespec="seconds")
        cur=db().execute("INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)",(username,hash_password(password),now))
        uid=cur.lastrowid
        db().execute("INSERT INTO user_settings(user_id,created_at,updated_at) VALUES(?,?,?)",(uid,now,now))
        db().commit()
        session["user_id"]=uid
        return jsonify(ok=True)
    except sqlite3.IntegrityError:
        return jsonify(ok=False,error="Username already exists."),409

@app.post("/api/auth/login")
def do_login():
    b=request.get_json(force=True) or {}
    username=str(b.get("username") or "").strip().lower()
    password=str(b.get("password") or "")
    row=db().execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
    if not row or not verify_password(password,row["password_hash"]):
        return jsonify(ok=False,error="Invalid username or password."),401
    session["user_id"]=row["id"]
    return jsonify(ok=True)

@app.post("/api/auth/logout")
def logout():
    session.clear(); return jsonify(ok=True)

@app.get("/api/auth/me")
def me():
    u=current_user()
    if not u: return jsonify(ok=False),401
    return jsonify(ok=True,username=u["username"])

@app.get("/api/settings")
def get_settings():
    u=current_user()
    if not u: return jsonify(ok=False,error="Login required"),401
    key, secret=user_credentials()
    return jsonify(ok=True, steadfast_api_key=key, steadfast_secret_key=secret, base_url=STEADFAST_BASE_URL)

@app.post("/api/settings")
def save_settings():
    if not current_user(): return jsonify(ok=False,error="Login required"),401
    b=request.get_json(force=True) or {}
    key=str(b.get("steadfast_api_key") or "").strip()
    secret=str(b.get("steadfast_secret_key") or "").strip()
    now=datetime.now().isoformat(timespec="seconds")
    db().execute("INSERT INTO user_settings(user_id,steadfast_api_key,steadfast_secret_key,created_at,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET steadfast_api_key=excluded.steadfast_api_key, steadfast_secret_key=excluded.steadfast_secret_key, updated_at=excluded.updated_at",(session["user_id"],key,secret,now,now))
    db().commit(); return jsonify(ok=True,message="Steadfast API saved for this user.")

@app.post("/api/settings/test")
def test_settings():
    if not current_user(): return jsonify(ok=False,error="Login required"),401
    b=request.get_json(force=True) or {}
    key=str(b.get("steadfast_api_key") or "").strip()
    secret=str(b.get("steadfast_secret_key") or "").strip()
    if not key or not secret: return jsonify(ok=False,error="API Key and Secret Key are required."),400
    try:
        r=requests.get(STEADFAST_BASE_URL.rstrip("/")+"/get_balance",headers={"Api-Key":key,"Secret-Key":secret,"Content-Type":"application/json","Accept":"application/json"},timeout=20)
        try: data=r.json()
        except Exception: data={"message":r.text}
        if not r.ok: return jsonify(ok=False,error=f"Steadfast rejected the credentials (HTTP {r.status_code}).",details=data),400
        return jsonify(ok=True,message="Steadfast API connected successfully.",balance=data)
    except requests.RequestException as e:
        return jsonify(ok=False,error=f"Connection failed: {e}"),502

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify(ok=True, steadfast_configured=sf_ready())

@app.get("/api/config")
def config():
    u=current_user()
    return jsonify(steadfast_configured=sf_ready(), username=(u["username"] if u else ""))

@app.get("/api/locations/districts")
def districts():
    # Local Steadfast-style English area dataset: no external geo service required.
    rows = [{"id": i + 1, "name": name} for i, name in enumerate(sorted(BD_GEO_EN.keys()))]
    return jsonify({"data": rows, "source": "local"})

@app.get("/api/locations/upazilas")
def upazilas():
    district = request.args.get("district", "").strip()
    areas = BD_GEO_EN.get(district, [])
    return jsonify({"data": [{"id": i + 1, "name": x} for i, x in enumerate(areas)], "source": "local"})

@app.get("/api/locations/steadfast")
def steadfast_locations():
    # Steadfast exposes a police-stations endpoint. If credentials are configured,
    # this can be used to inspect their current station list.
    data, err = sf_get("/police_stations")
    if err:
        return jsonify(ok=False, error=err), 503
    return jsonify(ok=True, data=data)

@app.post("/api/parcels")
def create_parcel():
    body = request.get_json(force=True) or {}
    required = ["recipient_name", "recipient_phone", "recipient_address"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return jsonify(ok=False, error="Missing: " + ", ".join(missing)), 400

    invoice = str(body.get("invoice") or make_invoice()).strip()
    district = str(body.get("district") or "").strip()
    thana = str(body.get("thana") or "").strip()
    address = str(body["recipient_address"]).strip()
    location_prefix = ", ".join([x for x in [thana, district] if x])
    if location_prefix and location_prefix.lower() not in address.lower():
        address = f"{address}, {location_prefix}"

    payload = {
        "invoice": invoice,
        "recipient_name": str(body["recipient_name"]).strip(),
        "recipient_phone": str(body["recipient_phone"]).strip(),
        "recipient_address": address[:250],
        "cod_amount": float(body.get("cod_amount") or 0),
        "note": str(body.get("note") or "")[:500],
        "item_description": str(body.get("item_description") or "")[:500],
        "total_lot": int(body.get("total_lot") or 1),
        "delivery_type": int(body.get("delivery_type") or 0),
    }
    alt = str(body.get("alternative_phone") or "").strip()
    if alt: payload["alternative_phone"] = alt
    email = str(body.get("recipient_email") or "").strip()
    if email: payload["recipient_email"] = email

    sf_data, err = sf_post("/create_order", payload)
    if err:
        return jsonify(ok=False, error=err), 502

    cid, tracking, status = parse_consignment(sf_data)
    now = datetime.now().isoformat(timespec="seconds")
    conn = db()
    try:
        conn.execute("""
          INSERT INTO parcels
          (invoice,recipient_name,recipient_phone,alternative_phone,district,thana,
           recipient_address,cod_amount,weight,note,item_description,total_lot,delivery_type,
           supplier_cost,supplier_name,consignment_id,tracking_code,status,raw_response,created_at,updated_at,user_id)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            invoice, payload["recipient_name"], payload["recipient_phone"], alt,
            district, thana, address, payload["cod_amount"], float(body.get("weight") or 1),
            payload["note"], payload["item_description"], payload["total_lot"], payload["delivery_type"],
            float(body.get("supplier_cost") or 0), str(body.get("supplier_name") or ""),
            cid, tracking, status, json.dumps(sf_data, ensure_ascii=False), now, now, session["user_id"]
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify(ok=False, error="Invoice already exists. Try again."), 409

    row = conn.execute("SELECT * FROM parcels WHERE invoice=?", (invoice,)).fetchone()
    return jsonify(ok=True, parcel=dict(row), steadfast=sf_data)

@app.get("/api/parcels")
def list_parcels():
    q = request.args.get("q","").strip()
    status = request.args.get("status","").strip()
    conn = db()
    sql = "SELECT * FROM parcels WHERE user_id=?"
    args = [session["user_id"]]
    if q:
        sql += " AND (recipient_name LIKE ? OR recipient_phone LIKE ? OR invoice LIKE ? OR tracking_code LIKE ? OR consignment_id LIKE ?)"
        like = f"%{q}%"
        args += [like]*5
    if status:
        sql += " AND status=?"
        args.append(status)
    sql += " ORDER BY id DESC LIMIT 500"
    rows = [dict(r) for r in conn.execute(sql,args).fetchall()]
    return jsonify(rows)

@app.get("/api/parcels/<int:pid>")
def parcel(pid):
    row = db().execute("SELECT * FROM parcels WHERE id=? AND user_id=?", (pid,session["user_id"])).fetchone()
    if not row: return jsonify(ok=False,error="Parcel not found"),404
    return jsonify(ok=True, parcel=dict(row))

@app.post("/api/parcels/<int:pid>/refresh")
def refresh(pid):
    row = db().execute("SELECT * FROM parcels WHERE id=? AND user_id=?", (pid,session["user_id"])).fetchone()
    if not row: return jsonify(ok=False,error="Parcel not found"),404
    data, err = sf_get(f"/status_by_cid/{row['consignment_id']}") if row["consignment_id"] else (None,"No CN#")
    if err: return jsonify(ok=False,error=err),502
    cid, tracking, status = parse_consignment(data)
    now = datetime.now().isoformat(timespec="seconds")
    db().execute("UPDATE parcels SET status=?, tracking_code=COALESCE(?,tracking_code), updated_at=?, raw_response=? WHERE id=?",
                 (status,tracking,now,json.dumps(data,ensure_ascii=False),pid))
    db().commit()
    new = db().execute("SELECT * FROM parcels WHERE id=? AND user_id=?", (pid,session["user_id"])).fetchone()
    return jsonify(ok=True,parcel=dict(new),steadfast=data)

@app.get("/api/dashboard")
def dashboard():
    conn = db()
    def one(sql,args=()):
        return conn.execute(sql,args).fetchone()[0]
    uid=(session["user_id"],)
    total = one("SELECT COUNT(*) FROM parcels WHERE user_id=?",uid)
    delivered = one("SELECT COUNT(*) FROM parcels WHERE user_id=? AND status LIKE 'delivered%'",uid)
    pending = one("SELECT COUNT(*) FROM parcels WHERE user_id=? AND status IN ('pending','in_review','created')",uid)
    cancelled = one("SELECT COUNT(*) FROM parcels WHERE user_id=? AND status LIKE 'cancelled%'",uid)
    sales = one("SELECT COALESCE(SUM(cod_amount),0) FROM parcels WHERE user_id=?",uid)
    supplier = one("SELECT COALESCE(SUM(supplier_cost),0) FROM parcels WHERE user_id=?",uid)
    expenses = one("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=?",uid)
    delivery_est = delivered * 0  # placeholder for future fee sync
    profit = sales - supplier - expenses - delivery_est
    return jsonify({
        "total_orders":total,"delivered":delivered,"pending":pending,"cancelled":cancelled,
        "sales":sales,"supplier_cost":supplier,"delivery_cost":delivery_est,
        "other_expenses":expenses,"net_profit":profit,
        "steadfast_configured":sf_ready()
    })

@app.get("/api/expenses")
def expenses():
    rows = [dict(r) for r in db().execute("SELECT * FROM expenses WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()]
    return jsonify(rows)

@app.post("/api/expenses")
def add_expense():
    b=request.get_json(force=True) or {}
    title=str(b.get("title") or "").strip()
    amount=float(b.get("amount") or 0)
    if not title or amount <= 0: return jsonify(ok=False,error="Title and positive amount required"),400
    now=datetime.now().isoformat(timespec="seconds")
    db().execute("INSERT INTO expenses(title,amount,note,created_at,user_id) VALUES(?,?,?,?,?)",
                 (title,amount,str(b.get("note") or ""),now,session["user_id"]))
    db().commit()
    return jsonify(ok=True)

@app.get("/api/suppliers")
def suppliers():
    return jsonify([dict(r) for r in db().execute("SELECT * FROM suppliers WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()])

@app.post("/api/suppliers")
def add_supplier():
    b=request.get_json(force=True) or {}
    name=str(b.get("name") or "").strip()
    if not name: return jsonify(ok=False,error="Supplier name required"),400
    now=datetime.now().isoformat(timespec="seconds")
    db().execute("INSERT INTO suppliers(name,phone,address,paid,due,created_at,user_id) VALUES(?,?,?,?,?,?,?)",
                 (name,str(b.get("phone") or ""),str(b.get("address") or ""),float(b.get("paid") or 0),float(b.get("due") or 0),now,session["user_id"]))
    db().commit()
    return jsonify(ok=True)

if __name__ == "__main__":
    port=int(os.environ.get("PORT","5000"))
    app.run(host="0.0.0.0", port=port)
