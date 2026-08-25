
import os, re, logging, secrets
from datetime import datetime, timezone
from decimal import Decimal
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from geo_data import BD_GEO

load_dotenv()
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = BASE_DIR

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "business.db")

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

STEADFAST_BASE_URL = os.getenv("STEADFAST_BASE_URL", "https://portal.packzy.com/api/v1").rstrip("/")
API_KEY = os.getenv("STEADFAST_API_KEY", "").strip()
SECRET_KEY = os.getenv("STEADFAST_SECRET_KEY", "").strip()
WEBHOOK_TOKEN = os.getenv("STEADFAST_WEBHOOK_TOKEN", "").strip()
APP_SECRET = os.getenv("APP_SECRET", "").strip() or secrets.token_hex(32)
app.secret_key = APP_SECRET
PORT = int(os.getenv("PORT", "5000"))
GEO_URL = os.getenv("GEO_URL", "")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(190), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SteadfastAccount(Base):
    __tablename__ = "steadfast_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    api_key = Column(String(255), nullable=False)
    secret_key = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True, index=True)
    invoice = Column(String(100), unique=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    alternative_phone = Column(String(20))
    address = Column(String(250), nullable=False)
    district = Column(String(100), nullable=False)
    thana = Column(String(100), nullable=False)
    cod_amount = Column(Float, nullable=False, default=0)
    supplier_name = Column(String(120))
    supplier_cost = Column(Float, nullable=False, default=0)
    delivery_charge = Column(Float, nullable=False, default=0)
    quantity = Column(Integer, nullable=False, default=1)
    weight = Column(Float, nullable=False, default=0)
    item_description = Column(String(400))
    note = Column(String(480))
    exchange = Column(Boolean, default=False)
    status = Column(String(40), nullable=False, default="pending")
    steadfast_status = Column(String(80))
    consignment_id = Column(String(80))
    tracking_code = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True, index=True)
    title = Column(String(150), nullable=False)
    amount = Column(Float, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SupplierPayment(Base):
    __tablename__ = "supplier_payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True, index=True)
    supplier_name = Column(String(120), nullable=False)
    amount = Column(Float, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(engine)

def ensure_legacy_columns():
    # Existing deployments may already have tables from the older single-user build.
    # Add user_id columns when possible; fresh databases are handled by create_all().
    try:
        from sqlalchemy import inspect, text
        insp = inspect(engine)
        with engine.begin() as conn:
            migrations = {
                "orders": ["user_id", "consignment_id", "tracking_code", "steadfast_status"],
                "expenses": ["user_id"],
                "supplier_payments": ["user_id"],
            }
            for table, columns in migrations.items():
                if not insp.has_table(table):
                    continue
                existing = {c["name"] for c in insp.get_columns(table)}
                for column in columns:
                    if column in existing:
                        continue
                    if engine.dialect.name == "sqlite":
                        # SQLite supports ADD COLUMN for these nullable fields.
                        sql_type = "INTEGER" if column == "user_id" else "VARCHAR(100)"
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))
                    elif engine.dialect.name == "postgresql":
                        sql_type = "INTEGER" if column == "user_id" else "VARCHAR(100)"
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {sql_type}"))
    except Exception:
        logging.exception("legacy schema migration failed")

ensure_legacy_columns()

def clean(v):
    return str(v or "").strip()

def phone(v):
    return re.sub(r"\D", "", clean(v))

def current_user_id():
    try:
        return int(session.get("user_id")) if session.get("user_id") else None
    except Exception:
        return None

def require_login():
    if not current_user_id():
        return jsonify({"ok": False, "message": "Login করুন।"}), 401
    return None

def user_credentials():
    uid = current_user_id()
    if uid:
        db = SessionLocal()
        try:
            a = db.query(SteadfastAccount).filter_by(user_id=uid).first()
            if a:
                return a.api_key, a.secret_key
        finally:
            db.close()
    return API_KEY, SECRET_KEY

def headers(api_key=None, secret_key=None):
    api_key, secret_key = api_key if api_key is not None else user_credentials()[0], secret_key if secret_key is not None else user_credentials()[1]
    return {
        "Api-Key": api_key,
        "Secret-Key": secret_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def steadfast_configured():
    a, s = user_credentials()
    return bool(a and s)

def order_dict(o):
    return {
        "id": o.id, "invoice": o.invoice, "customer_name": o.customer_name,
        "phone": o.phone, "alternative_phone": o.alternative_phone or "",
        "address": o.address, "district": o.district, "thana": o.thana,
        "cod_amount": o.cod_amount, "supplier_name": o.supplier_name or "",
        "supplier_cost": o.supplier_cost, "delivery_charge": o.delivery_charge,
        "quantity": o.quantity, "weight": o.weight,
        "item_description": o.item_description or "", "note": o.note or "",
        "exchange": bool(o.exchange), "status": o.status,
        "steadfast_status": o.steadfast_status or "",
        "consignment_id": o.consignment_id or "", "tracking_code": o.tracking_code or "",
        "created_at": o.created_at.isoformat() if o.created_at else "",
        "updated_at": o.updated_at.isoformat() if o.updated_at else "",
    }

def validate_order(d):
    required = ["invoice","customer_name","phone","address","district","thana","cod_amount","supplier_cost","delivery_charge"]
    missing = [x for x in required if d.get(x) in (None, "")]
    if missing:
        return "Missing fields: " + ", ".join(missing)
    p = phone(d["phone"])
    if len(p) != 11 or not p.startswith("01"):
        return "Phone must be an 11-digit Bangladesh mobile number."
    try:
        for key in ("cod_amount","supplier_cost","delivery_charge","weight"):
            float(d.get(key, 0) or 0)
        int(d.get("quantity", 1) or 1)
    except Exception:
        return "Amount, weight and quantity must be valid numbers."
    if float(d.get("cod_amount",0)) < 0 or float(d.get("supplier_cost",0)) < 0 or float(d.get("delivery_charge",0)) < 0:
        return "Amounts cannot be negative."
    if len(clean(d["invoice"])) > 100 or len(clean(d["customer_name"])) > 100 or len(clean(d["address"])) > 250:
        return "Invoice/name/address is too long."
    return None

@app.post("/api/auth/register")
def register():
    d = request.get_json(silent=True) or {}
    name, email, password = clean(d.get("name")), clean(d.get("email")).lower(), clean(d.get("password"))
    if not name or not email or len(password) < 6:
        return jsonify({"ok": False, "message": "নাম, সঠিক email এবং কমপক্ষে ৬ অক্ষরের password দিন।"}), 400
    db = SessionLocal()
    try:
        if db.query(User).filter_by(email=email).first():
            return jsonify({"ok": False, "message": "এই email দিয়ে account আগে থেকেই আছে। Login করুন।"}), 409
        u = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.add(u); db.commit(); db.refresh(u)
        session["user_id"] = u.id
        return jsonify({"ok": True, "user": {"id": u.id, "name": u.name, "email": u.email}})
    except Exception as e:
        db.rollback(); logging.exception("register failed")
        return jsonify({"ok": False, "message": "Register failed.", "details": str(e)}), 500
    finally: db.close()

@app.post("/api/auth/login")
def login():
    d = request.get_json(silent=True) or {}
    email, password = clean(d.get("email")).lower(), clean(d.get("password"))
    db = SessionLocal()
    try:
        u = db.query(User).filter_by(email=email).first()
        if not u or not check_password_hash(u.password_hash, password):
            return jsonify({"ok": False, "message": "Email অথবা password ভুল।"}), 401
        session["user_id"] = u.id
        return jsonify({"ok": True, "user": {"id": u.id, "name": u.name, "email": u.email}})
    finally: db.close()

@app.get("/api/auth/me")
def auth_me():
    uid = current_user_id()
    if not uid: return jsonify({"ok": True, "logged_in": False})
    db = SessionLocal()
    try:
        u = db.get(User, uid)
        if not u:
            session.pop("user_id", None); return jsonify({"ok": True, "logged_in": False})
        return jsonify({"ok": True, "logged_in": True, "user": {"id": u.id, "name": u.name, "email": u.email}})
    finally: db.close()

@app.post("/api/auth/logout")
def auth_logout():
    session.clear(); return jsonify({"ok": True})

@app.get("/api/steadfast/settings")
def get_steadfast_settings():
    if (x := require_login()): return x
    uid = current_user_id(); db = SessionLocal()
    try:
        a = db.query(SteadfastAccount).filter_by(user_id=uid).first()
        return jsonify({"ok": True, "configured": bool(a), "api_key": ((a.api_key[:4] + "***") if a else "")})
    finally: db.close()

@app.post("/api/steadfast/settings")
def save_steadfast_settings():
    if (x := require_login()): return x
    d = request.get_json(silent=True) or {}; api_key=clean(d.get("api_key")); secret_key=clean(d.get("secret_key"))
    if not api_key or not secret_key: return jsonify({"ok": False, "message": "API Key এবং Secret Key দিন।"}), 400
    uid=current_user_id(); db=SessionLocal()
    try:
        a=db.query(SteadfastAccount).filter_by(user_id=uid).first()
        if not a: a=SteadfastAccount(user_id=uid, api_key=api_key, secret_key=secret_key); db.add(a)
        else: a.api_key=api_key; a.secret_key=secret_key
        db.commit(); return jsonify({"ok": True, "message": "Steadfast API credentials save হয়েছে।"})
    finally: db.close()

@app.post("/api/steadfast/test")
def test_steadfast():
    if (x := require_login()): return x
    d=request.get_json(silent=True) or {}; api_key=clean(d.get("api_key")); secret_key=clean(d.get("secret_key"))
    if not api_key or not secret_key: return jsonify({"ok": False, "message": "API Key এবং Secret Key দিন।"}), 400
    try:
        r=requests.get(f"{STEADFAST_BASE_URL}/get_balance", headers=headers(api_key, secret_key), timeout=30)
        try: result=r.json()
        except Exception: result={"raw":r.text}
        if not r.ok: return jsonify({"ok":False,"message":"Steadfast API credentials কাজ করছে না।","details":result}), r.status_code
        return jsonify({"ok":True,"message":"Steadfast API connection ঠিক আছে।","balance":result})
    except requests.RequestException as e:
        return jsonify({"ok":False,"message":"Steadfast-এ connect করা যাচ্ছে না।","details":str(e)}),502

@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "steadfast-business",
        "steadfast_configured": steadfast_configured(),
        "database": "postgresql" if DATABASE_URL.startswith("postgres") else "sqlite"
    })

@app.get("/api/geo")
def geo():
    # Keep district/thana data inside the app so the selector does not depend
    # on a third-party geography URL being reachable from Railway.
    districts = [
        {
            "name": district,
            "bn_name": district,
            "upazilas": [{"name": area, "bn_name": area} for area in areas],
        }
        for district, areas in sorted(BD_GEO.items(), key=lambda x: x[0])
    ]
    return jsonify([{"name": "Bangladesh", "bn_name": "বাংলাদেশ", "districts": districts}])

@app.get("/api/police_stations")
def police_stations():
    if not steadfast_configured():
        return jsonify({"ok": False, "message": "Steadfast credentials are not configured."}), 503
    try:
        r = requests.get(f"{STEADFAST_BASE_URL}/police_stations", headers=headers(), timeout=30)
        try: data = r.json()
        except Exception: data = {"raw": r.text}
        return jsonify(data), r.status_code
    except requests.RequestException as e:
        return jsonify({"ok": False, "message": str(e)}), 502

@app.post("/api/orders")
def create_order():
    if (x := require_login()): return x
    """Save locally first. Courier submission happens separately."""
    d=request.get_json(silent=True) or {}; err=validate_order(d)
    if err:return jsonify({"ok":False,"message":err}),400
    invoice=clean(d["invoice"]); db=SessionLocal()
    try:
        if db.query(Order).filter_by(user_id=current_user_id(), invoice=invoice).first():
            return jsonify({"ok":False,"message":"এই Invoice আগে থেকেই আছে। অন্য Invoice দিন।"}),409
        o=Order(user_id=current_user_id(),invoice=invoice,customer_name=clean(d["customer_name"]),phone=phone(d["phone"]),
          alternative_phone=phone(d.get("alternative_phone")),address=clean(d["address"]),district=clean(d["district"]),
          thana=clean(d["thana"]),cod_amount=float(d["cod_amount"]),supplier_name=clean(d.get("supplier_name")),
          supplier_cost=float(d.get("supplier_cost",0)),delivery_charge=float(d.get("delivery_charge",0)),
          quantity=int(d.get("quantity",1) or 1),weight=float(d.get("weight",0) or 0),
          item_description=clean(d.get("item_description")),note=clean(d.get("note")),exchange=bool(d.get("exchange")),status="saved")
        db.add(o);db.commit();db.refresh(o)
        return jsonify({"ok":True,"order":order_dict(o),"message":"Order saved. Courier-এ এখনো পাঠানো হয়নি।"})
    except Exception as e:
        db.rollback();logging.exception("create order failed")
        return jsonify({"ok":False,"message":"Order save failed.","details":str(e)}),500
    finally:db.close()

@app.post("/api/orders/<int:order_id>/send")
def send_order_to_steadfast(order_id):
    if (x := require_login()): return x
    if not steadfast_configured():return jsonify({"ok":False,"message":"Steadfast API credentials are not configured."}),503
    db=SessionLocal()
    try:
        o=db.query(Order).filter_by(id=order_id, user_id=current_user_id()).first()
        if not o:return jsonify({"ok":False,"message":"Order not found."}),404
        if o.status not in ("saved","pending"):
            return jsonify({"ok":False,"message":"এই order আগে থেকেই courier workflow-এ আছে।"}),409
        full_address=f"{o.address}, {o.thana}, {o.district}"
        # IMPORTANT: delivery_charge is intentionally NOT sent to Steadfast.
        payload={"invoice":o.invoice,"recipient_name":o.customer_name,"recipient_phone":o.phone,
          "recipient_address":full_address[:250],"cod_amount":o.cod_amount,"note":o.note or "",
          "item_description":o.item_description or "","total_lot":o.quantity,"delivery_type":0}
        if o.alternative_phone:payload["alternative_phone"]=o.alternative_phone
        try:
            r=requests.post(f"{STEADFAST_BASE_URL}/create_order",headers=headers(),json=payload,timeout=30)
            try:result=r.json()
            except Exception:result={"raw":r.text}
        except requests.RequestException as e:
            return jsonify({"ok":False,"message":"Steadfast-এ পৌঁছানো যাচ্ছে না।","details":str(e)}),502
        if not r.ok:return jsonify({"ok":False,"message":"Steadfast order failed.","steadfast_status":r.status_code,"details":result}),r.status_code
        # Steadfast may return identifiers nested under `consignment`, `data`, or another
        # response wrapper. Extract them recursively so CN# and Tracking ID are not lost.
        def find_value(obj, keys):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if str(k).lower() in keys and v not in (None, ""):
                        return v
                for v in obj.values():
                    found = find_value(v, keys)
                    if found not in (None, ""):
                        return found
            elif isinstance(obj, list):
                for v in obj:
                    found = find_value(v, keys)
                    if found not in (None, ""):
                        return found
            return None

        cons = result.get("consignment") if isinstance(result, dict) else None
        cons = cons if isinstance(cons, dict) else {}
        consignment_id = find_value(result, {"consignment_id", "consignmentid", "cn", "cn_number", "parcel_id", "parcelid"})
        tracking_code = find_value(result, {"tracking_code", "trackingcode", "tracking_id", "trackingid"})
        status_value = find_value(result, {"status", "delivery_status", "deliverystatus"})

        # If create_order did not include CN#/Tracking, immediately ask Steadfast for the
        # invoice status. This handles gateways that return only a success message on create.
        if not consignment_id or not tracking_code:
            try:
                sr = requests.get(
                    f"{STEADFAST_BASE_URL}/status_by_invoice/{o.invoice}",
                    headers=headers(), timeout=30
                )
                if sr.ok:
                    try:
                        status_result = sr.json()
                    except Exception:
                        status_result = {}
                    consignment_id = consignment_id or find_value(status_result, {"consignment_id", "consignmentid", "cn", "cn_number", "parcel_id", "parcelid"})
                    tracking_code = tracking_code or find_value(status_result, {"tracking_code", "trackingcode", "tracking_id", "trackingid"})
                    status_value = status_value or find_value(status_result, {"status", "delivery_status", "deliverystatus"})
            except requests.RequestException:
                pass

        o.consignment_id = clean(consignment_id)
        o.tracking_code = clean(tracking_code)
        o.steadfast_status = clean(status_value)
        o.status = "submitted"
        db.commit();db.refresh(o)
        return jsonify({"ok":True,"message":"Steadfast-এ order পাঠানো হয়েছে।","order":order_dict(o)})
    except Exception as e:
        db.rollback();logging.exception("send order failed")
        return jsonify({"ok":False,"message":"Courier send failed.","details":str(e)}),500
    finally:db.close()

@app.patch("/api/orders/<int:order_id>/delivery-charge")
def edit_delivery_charge(order_id):
    if (x := require_login()): return x
    d = request.get_json(silent=True) or {}
    try:
        amount = float(d.get("delivery_charge"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "সঠিক Delivery Charge দিন।"}), 400
    if amount < 0:
        return jsonify({"ok": False, "message": "Delivery Charge negative হতে পারবে না।"}), 400
    db = SessionLocal()
    try:
        o = db.query(Order).filter_by(id=order_id, user_id=current_user_id()).first()
        if not o:
            return jsonify({"ok": False, "message": "Order not found."}), 404
        o.delivery_charge = amount
        db.commit(); db.refresh(o)
        return jsonify({"ok": True, "order": order_dict(o), "message": "Delivery Charge update হয়েছে।"})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "message": "Delivery Charge update failed.", "details": str(e)}), 500
    finally:
        db.close()

@app.patch("/api/orders/<int:order_id>")
def edit_saved_order(order_id):
    if (x := require_login()): return x
    d=request.get_json(silent=True) or {};db=SessionLocal()
    try:
        o=db.query(Order).filter_by(id=order_id, user_id=current_user_id()).first()
        if not o:return jsonify({"ok":False,"message":"Order not found."}),404
        if o.status not in ("saved","pending"):return jsonify({"ok":False,"message":"Courier-এ পাঠানো order edit করা যাবে না।"}),409
        for k,v in {"phone":phone(d.get("phone",o.phone)),"alternative_phone":phone(d.get("alternative_phone",o.alternative_phone)),"customer_name":clean(d.get("customer_name",o.customer_name)),"invoice":clean(d.get("invoice",o.invoice)),"address":clean(d.get("address",o.address)),"district":clean(d.get("district",o.district)),"thana":clean(d.get("thana",o.thana)),"cod_amount":float(d.get("cod_amount",o.cod_amount)),"supplier_cost":float(d.get("supplier_cost",o.supplier_cost)),"supplier_name":clean(d.get("supplier_name",o.supplier_name)),"delivery_charge":float(d.get("delivery_charge",o.delivery_charge)),"quantity":int(d.get("quantity",o.quantity)),"weight":float(d.get("weight",o.weight)),"item_description":clean(d.get("item_description",o.item_description)),"note":clean(d.get("note",o.note)),"exchange":bool(d.get("exchange",o.exchange))}.items():setattr(o,k,v)
        if len(o.phone)!=11 or not o.phone.startswith("01"):return jsonify({"ok":False,"message":"সঠিক ১১ সংখ্যার ফোন দিন।"}),400
        if not o.district or not o.thana:return jsonify({"ok":False,"message":"District এবং Thana নির্বাচন করুন।"}),400
        db.commit();db.refresh(o);return jsonify({"ok":True,"order":order_dict(o),"message":"Saved order update হয়েছে।"})
    except Exception as e:
        db.rollback();return jsonify({"ok":False,"message":"Update failed.","details":str(e)}),500
    finally:db.close()

@app.get("/api/orders")
def list_orders():
    if (x := require_login()): return x
    db = SessionLocal()
    try:
        q = db.query(Order).filter(Order.user_id == current_user_id()).order_by(Order.id.desc())
        status = clean(request.args.get("status"))
        if status: q = q.filter(Order.status == status)
        return jsonify({"ok": True, "orders": [order_dict(x) for x in q.limit(1000).all()]})
    finally:
        db.close()

def map_status(s):
    s = clean(s).lower().replace("_"," ").replace("-"," ")
    if "delivered" in s and "partial" not in s: return "delivered"
    if "partially delivered" in s: return "partial_delivered"
    if "partially cancelled" in s: return "partial_cancelled"
    if "cancel" in s: return "cancelled"
    if "return" in s: return "returned"
    if s in ("pending","in review","in_review","approved","in transit","in_transit","hold"): return "submitted"
    return "submitted"

@app.post("/api/orders/<int:order_id>/status")
def manual_status(order_id):
    if (x := require_login()): return x
    d = request.get_json(silent=True) or {}
    status = clean(d.get("status")).lower()
    allowed = {"saved","pending","submitted","delivered","partial_delivered","partial_cancelled","cancelled","returned"}
    if status not in allowed: return jsonify({"ok": False, "message": "Invalid status."}), 400
    db = SessionLocal()
    try:
        o = db.query(Order).filter_by(id=order_id, user_id=current_user_id()).first()
        if not o: return jsonify({"ok": False, "message": "Order not found."}), 404
        o.status = status
        db.commit()
        return jsonify({"ok": True, "order": order_dict(o)})
    finally: db.close()

@app.post("/api/orders/<int:order_id>/sync")
def sync_order(order_id):
    if (x := require_login()): return x
    if not steadfast_configured():
        return jsonify({"ok": False, "message": "Steadfast API credentials are not configured."}), 503
    db = SessionLocal()
    try:
        o = db.query(Order).filter_by(id=order_id, user_id=current_user_id()).first()
        if not o: return jsonify({"ok": False, "message": "Order not found."}), 404
        r = requests.get(f"{STEADFAST_BASE_URL}/status_by_invoice/{o.invoice}", headers=headers(), timeout=30)
        try: result = r.json()
        except Exception: result = {"raw": r.text}
        if not r.ok: return jsonify({"ok": False, "message": "Steadfast status request failed.", "details": result}), r.status_code
        def find_value(obj, keys):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if str(k).lower() in keys and v not in (None, ""):
                        return v
                for v in obj.values():
                    found = find_value(v, keys)
                    if found not in (None, ""):
                        return found
            elif isinstance(obj, list):
                for v in obj:
                    found = find_value(v, keys)
                    if found not in (None, ""):
                        return found
            return None

        s = find_value(result, {"status", "delivery_status", "deliverystatus"})
        cid = find_value(result, {"consignment_id", "consignmentid", "cn", "cn_number", "parcel_id", "parcelid"})
        tid = find_value(result, {"tracking_code", "trackingcode", "tracking_id", "trackingid"})
        if s:
            o.steadfast_status = clean(s)
            o.status = map_status(s)
        if tid: o.tracking_code = clean(tid)
        if cid: o.consignment_id = clean(cid)
        charge_value = cons.get("delivery_charge", result.get("delivery_charge"))
        if charge_value not in (None, ""):
            try:
                charge = float(charge_value)
                if charge >= 0: o.delivery_charge = charge
            except (TypeError, ValueError):
                pass
        db.commit()
        return jsonify({"ok": True, "order": order_dict(o), "steadfast": result})
    except requests.RequestException as e:
        return jsonify({"ok": False, "message": "Steadfast-এ পৌঁছানো যাচ্ছে না।", "details": str(e)}), 502
    finally: db.close()

@app.post("/webhooks/steadfast")
def steadfast_webhook():
    """Receive Steadfast delivery-status webhook updates.
    Delivery charge is taken from webhook payload and saved automatically.
    """
    if WEBHOOK_TOKEN:
        auth = request.headers.get("Authorization", "")
        expected = "Bearer " + WEBHOOK_TOKEN
        if auth != expected:
            return jsonify({"ok": False, "message": "Unauthorized webhook."}), 401

    d = request.get_json(silent=True) or {}
    invoice = clean(d.get("invoice"))
    consignment_id = clean(d.get("consignment_id"))
    tracking_code = clean(d.get("tracking_code"))
    if not invoice and not consignment_id and not tracking_code:
        return jsonify({"ok": False, "message": "invoice, consignment_id or tracking_code required."}), 400

    db = SessionLocal()
    try:
        q = None
        if invoice:
            q = db.query(Order).filter_by(user_id=current_user_id(), invoice=invoice).first()
        if not q and consignment_id:
            q = db.query(Order).filter_by(consignment_id=consignment_id).first()
        if not q and tracking_code:
            q = db.query(Order).filter_by(tracking_code=tracking_code).first()
        if not q:
            return jsonify({"ok": False, "message": "Order not found in app."}), 404

        status_value = clean(d.get("status"))
        if status_value:
            q.steadfast_status = status_value
            q.status = map_status(status_value)
        if consignment_id: q.consignment_id = consignment_id
        if tracking_code: q.tracking_code = tracking_code

        # Steadfast webhook provides the actual applied delivery charge.
        if d.get("delivery_charge") not in (None, ""):
            try:
                charge = float(d.get("delivery_charge"))
                if charge >= 0:
                    q.delivery_charge = charge
            except (TypeError, ValueError):
                pass

        q.updated_at = datetime.now(timezone.utc)
        db.commit(); db.refresh(q)
        return jsonify({"ok": True, "message": "Steadfast update received.", "order": order_dict(q)})
    except Exception as e:
        db.rollback()
        logging.exception("Steadfast webhook failed")
        return jsonify({"ok": False, "message": "Webhook processing failed.", "details": str(e)}), 500
    finally:
        db.close()

@app.get("/api/balance")
def balance():
    if (x := require_login()): return x
    if not steadfast_configured():
        return jsonify({"ok": False, "message": "Steadfast API credentials are not configured."}), 503
    try:
        r = requests.get(f"{STEADFAST_BASE_URL}/get_balance", headers=headers(), timeout=30)
        try: result = r.json()
        except Exception: result = {"raw": r.text}
        return jsonify(result), r.status_code
    except requests.RequestException as e:
        return jsonify({"ok": False, "message": str(e)}), 502

@app.post("/api/expenses")
def add_expense():
    if (x := require_login()): return x
    d = request.get_json(silent=True) or {}
    title, amount = clean(d.get("title")), d.get("amount")
    if not title: return jsonify({"ok": False, "message": "খরচের নাম দিন।"}), 400
    try: amount = float(amount)
    except: return jsonify({"ok": False, "message": "সঠিক amount দিন।"}), 400
    if amount < 0: return jsonify({"ok": False, "message": "Amount negative হতে পারবে না।"}), 400
    db = SessionLocal()
    try:
        x = Expense(user_id=current_user_id(), title=title, amount=amount, note=clean(d.get("note")))
        db.add(x); db.commit()
        return jsonify({"ok": True})
    finally: db.close()

@app.get("/api/expenses")
def expenses():
    if (x := require_login()): return x
    db = SessionLocal()
    try:
        rows = db.query(Expense).order_by(Expense.id.desc()).all()
        return jsonify({"ok": True, "expenses":[{"id":x.id,"title":x.title,"amount":x.amount,"note":x.note or "","created_at":x.created_at.isoformat()} for x in rows]})
    finally: db.close()

@app.post("/api/supplier-payments")
def add_supplier_payment():
    if (x := require_login()): return x
    d = request.get_json(silent=True) or {}
    name, amount = clean(d.get("supplier_name")), d.get("amount")
    if not name: return jsonify({"ok": False, "message": "Supplier নাম দিন।"}), 400
    try: amount = float(amount)
    except: return jsonify({"ok": False, "message": "সঠিক amount দিন।"}), 400
    if amount < 0: return jsonify({"ok": False, "message": "Amount negative হতে পারবে না।"}), 400
    db = SessionLocal()
    try:
        x = SupplierPayment(user_id=current_user_id(), supplier_name=name, amount=amount, note=clean(d.get("note")))
        db.add(x); db.commit()
        return jsonify({"ok": True})
    finally: db.close()

@app.get("/api/supplier-payments")
def supplier_payments():
    if (x := require_login()): return x
    db = SessionLocal()
    try:
        rows = db.query(SupplierPayment).order_by(SupplierPayment.id.desc()).all()
        return jsonify({"ok": True, "payments":[{"id":x.id,"supplier_name":x.supplier_name,"amount":x.amount,"note":x.note or "","created_at":x.created_at.isoformat()} for x in rows]})
    finally: db.close()

@app.get("/api/dashboard")
def dashboard():
    if (x := require_login()): return x
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.user_id == current_user_id()).all()
        expenses = db.query(Expense).filter(Expense.user_id == current_user_id()).all()
        payments = db.query(SupplierPayment).filter(SupplierPayment.user_id == current_user_id()).all()

        delivered = [o for o in orders if o.status in ("delivered","partial_delivered")]
        returns = [o for o in orders if o.status in ("cancelled","returned","partial_cancelled")]
        gross_sales = sum(o.cod_amount for o in delivered)
        supplier = sum(o.supplier_cost for o in delivered)
        delivery = sum(o.delivery_charge for o in delivered)
        order_profit = gross_sales - supplier - delivery
        return_loss = sum(o.delivery_charge for o in returns)
        other_expense = sum(x.amount for x in expenses)
        net_profit = order_profit - return_loss - other_expense

        supplier_cost_all = sum(o.supplier_cost for o in orders if o.status in ("delivered","partial_delivered"))
        supplier_paid = sum(x.amount for x in payments)
        supplier_due = supplier_cost_all - supplier_paid

        return jsonify({"ok":True, "stats":{
            "total_orders":len(orders), "delivered":len(delivered), "pending":len([o for o in orders if o.status in ("saved","pending","submitted")]),
            "cancelled_returned":len(returns), "gross_sales":gross_sales, "supplier_cost":supplier,
            "delivery_charge":delivery, "order_profit":order_profit, "return_loss":return_loss,
            "other_expense":other_expense, "net_profit":net_profit, "supplier_paid":supplier_paid, "supplier_due":supplier_due
        }})
    finally: db.close()

@app.get("/api/backup")
def download_backup():
    """Download the logged-in user's application data as JSON.
    If authentication is present in the app, use its current-user hook.
    Otherwise this endpoint backs up the local application tables.
    """
    db = SessionLocal()
    try:
        payload = {
            "backup_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "orders": [order_dict(o) for o in db.query(Order).order_by(Order.id.asc()).all()],
            "expenses": [
                {"id": x.id, "title": x.title, "amount": x.amount,
                 "note": x.note or "", "created_at": x.created_at.isoformat() if x.created_at else ""}
                for x in db.query(Expense).order_by(Expense.id.asc()).all()
            ],
            "supplier_payments": [
                {"id": x.id, "supplier_name": x.supplier_name, "amount": x.amount,
                 "note": x.note or "", "created_at": x.created_at.isoformat() if x.created_at else ""}
                for x in db.query(SupplierPayment).order_by(SupplierPayment.id.asc()).all()
            ],
        }
        resp = jsonify(payload)
        resp.headers["Content-Disposition"] = 'attachment; filename="steadfast_business_backup.json"'
        resp.headers["Content-Type"] = "application/json; charset=utf-8"
        return resp
    finally:
        db.close()

@app.post("/api/restore")
def restore_backup():
    """Restore application data from a JSON backup.
    Existing rows with the same invoice are updated; missing rows are inserted.
    """
    d = request.get_json(silent=True) or {}
    if not isinstance(d, dict) or "backup_version" not in d:
        return jsonify({"ok": False, "message": "Invalid backup file."}), 400

    db = SessionLocal()
    try:
        # Orders: upsert by invoice
        for item in d.get("orders", []):
            invoice = clean(item.get("invoice"))
            if not invoice:
                continue
            o = db.query(Order).filter_by(invoice=invoice).first()
            if not o:
                o = Order(invoice=invoice)
                db.add(o)
            for field in [
                "customer_name","phone","alternative_phone","address","district","thana",
                "cod_amount","supplier_name","supplier_cost","delivery_charge","quantity",
                "weight","item_description","note","exchange","status",
                "steadfast_status","consignment_id","tracking_code"
            ]:
                if field in item:
                    setattr(o, field, item.get(field))
        db.flush()

        # Expenses: append restored records
        for item in d.get("expenses", []):
            title = clean(item.get("title"))
            if title:
                db.add(Expense(title=title, amount=float(item.get("amount", 0) or 0),
                               note=clean(item.get("note"))))

        # Supplier payments: append restored records
        for item in d.get("supplier_payments", []):
            name = clean(item.get("supplier_name"))
            if name:
                db.add(SupplierPayment(supplier_name=name, amount=float(item.get("amount", 0) or 0),
                                       note=clean(item.get("note"))))

        db.commit()
        return jsonify({"ok": True, "message": "Backup restored successfully."})
    except Exception as e:
        db.rollback()
        logging.exception("backup restore failed")
        return jsonify({"ok": False, "message": "Restore failed.", "details": str(e)}), 500
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
