import os
import datetime
from functools import wraps
import sqlite3
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, abort
from jinja2 import DictLoader
from werkzeug.security import generate_password_hash, check_password_hash

APP_NAME = "Bandhan Marriag Consultant"
SECRET_KEY = "change-this-secret-key"
ADMIN_EMAIL = "admin@rishta.com"
ADMIN_PASSWORD = "admin123"
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "matrimonial.db")

STATUSES = ["pending", "accepted", "rejected", "married"]
RELIGIONS = ["Sunni", "Shia", "Ahle Hadith", "Other"]
MARITAL = ["Never Married", "Divorced", "Widowed"]
PFIELDS = ["full_name","gender","age","city","religion","education","occupation","marital_status","height","phone","about","partner_pref"]

app = Flask(__name__)
app.secret_key = SECRET_KEY

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_e):
    d=g.pop("db",None)
    if d: d.close()

def q(sql,args=(),one=False):
    cur=db().cursor()
    cur.execute(sql,args)
    rows=cur.fetchall()
    cur.close()
    return rows[0] if one and rows else (None if one else rows)

def run(sql,args=()):
    cur=db().cursor()
    cur.execute(sql,args)
    db().commit()
    lid=cur.lastrowid
    cur.close()
    return lid

def count(sql,args=()):
    r=q(sql,args,one=True)
    return 0 if not r else r[0]

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def init_db():
    con=sqlite3.connect(DB_FILE)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, role TEXT, phone TEXT, active INTEGER DEFAULT 1, created_at TEXT);
    CREATE TABLE IF NOT EXISTS profiles(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, matchmaker_id INTEGER, full_name TEXT, gender TEXT, age INTEGER, city TEXT, religion TEXT, education TEXT, occupation TEXT, marital_status TEXT, height TEXT, phone TEXT, about TEXT, partner_pref TEXT, status TEXT DEFAULT 'pending', created_at TEXT);
    CREATE TABLE IF NOT EXISTS proposals(id INTEGER PRIMARY KEY AUTOINCREMENT, from_profile INTEGER, to_profile INTEGER, matchmaker_id INTEGER, kind TEXT, status TEXT DEFAULT 'pending', note TEXT, created_at TEXT);
    """)
    if not con.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
        con.execute("INSERT INTO users(name,email,password,role,phone,created_at) VALUES(?,?,?,?,?,?)", ("Administrator",ADMIN_EMAIL,generate_password_hash(ADMIN_PASSWORD),"admin","",now()))
    con.commit()
    con.close()
    print("Database ready - SQLite mode")

def login_required(*roles):
    def deco(f):
        @wraps(f)
        def wrapper(*a,**k):
            if "uid" not in session: return redirect(url_for("login"))
            if roles and session["role"] not in roles: abort(403)
            return f(*a,**k)
        return wrapper
    return deco

@app.context_processor
def inject():
    return dict(app_name=APP_NAME, STATUSES=STATUSES, RELIGIONS=RELIGIONS, MARITAL=MARITAL)

def form_profile():
    d={k:request.form.get(k,"").strip() for k in PFIELDS}
    if not d["full_name"] or d["gender"] not in ("Male","Female"): raise ValueError("Name and gender are required.")
    try: d["age"]=int(d["age"])
    except: raise ValueError("Age must be a number.")
    if not 18<=d["age"]<=80: raise ValueError("Age must be between 18 and 80.")
    return d

def delete_profile(pid):
    run("DELETE FROM proposals WHERE from_profile=? OR to_profile=?",(pid,pid))
    run("DELETE FROM profiles WHERE id=?",(pid,))

def score(a,b):
    s=0
    if a["city"] and a["city"].lower()==(b["city"] or "").lower(): s+=30
    diff=abs(a["age"]-b["age"])
    s+=30 if diff<=3 else 15 if diff<=6 else 0
    if a["religion"]==b["religion"]: s+=25
    if a["marital_status"]==b["marital_status"]: s+=15
    return s

PROPOSAL_SQL = "SELECT pr.*, a.full_name AS a_name, a.age AS a_age, a.city AS a_city, a.phone AS a_phone, b.full_name AS b_name, b.age AS b_age, b.city AS b_city, b.phone AS b_phone, u.name AS mm_name FROM proposals pr JOIN profiles a ON a.id = pr.from_profile JOIN profiles b ON b.id = pr.to_profile LEFT JOIN users u ON u.id = pr.matchmaker_id"

@app.route("/")
def home():
    if "uid" in session: return redirect(url_for("dashboard"))
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=q("SELECT * FROM users WHERE email=?",(request.form.get("email","").strip().lower(),),one=True)
        if u and check_password_hash(u["password"],request.form.get("password","")):
            if not u["active"]: flash("Your account is disabled.","bad")
            else:
                session.clear()
                session.update(uid=u["id"],role=u["role"],name=u["name"])
                return redirect(url_for("dashboard"))
        else: flash("Wrong email or password.","bad")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        pw=request.form.get("password","")
        try:
            d=form_profile()
            if "@" not in email: raise ValueError("Enter a valid email.")
            if len(pw)<6: raise ValueError("Password must be at least 6 characters.")
            if q("SELECT 1 FROM users WHERE email=?",(email,),one=True): raise ValueError("This email is already registered.")
        except ValueError as e:
            flash(str(e),"bad")
            return render_template("register.html",p=request.form)
        uid=run("INSERT INTO users(name,email,password,role,phone,created_at) VALUES(?,?,?,?,?,?)",(d["full_name"],email,generate_password_hash(pw),"client",d["phone"],now()))
        cols=",".join(PFIELDS)
        run(f"INSERT INTO profiles(user_id,{cols},status,created_at) VALUES(?,{','.join('?'*len(PFIELDS))},'pending',?)",(uid,*[d[k] for k in PFIELDS],now()))
        flash("Account created. Please login.","ok")
        return redirect(url_for("login"))
    return render_template("register.html",p=None)

@app.route("/dashboard")
@login_required()
def dashboard():
    target={"admin":"admin_home","matchmaker":"mm_home","client":"client_home"}[session["role"]]
    return redirect(url_for(target))

@app.route("/profile/<int:pid>")
@login_required()
def profile_view(pid):
    p=q("SELECT * FROM profiles WHERE id=?",(pid,),one=True)
    if not p: abort(404)
    if session["role"]=="client" and p["status"]!="approved" and p["user_id"]!=session["uid"]: abort(403)
    return render_template("profile_view.html",p=p)

@app.route("/profile/<int:pid>/edit", methods=["GET","POST"])
@login_required()
def profile_edit(pid):
    p=q("SELECT * FROM profiles WHERE id=?",(pid,),one=True)
    if not p: abort(404)
    role,uid=session["role"],session["uid"]
    allowed=(role=="admin" or (role=="matchmaker" and p["matchmaker_id"]==uid) or (role=="client" and p["user_id"]==uid))
    if not allowed: abort(403)
    if request.method=="POST":
        try: d=form_profile()
        except ValueError as e:
            flash(str(e),"bad")
            return render_template("profile_form.html",p=request.form,title="Edit Profile")
        sets=",".join(f"{k}=?" for k in PFIELDS)
        run(f"UPDATE profiles SET {sets} WHERE id=?",(*[d[k] for k in PFIELDS],pid))
        if role=="client":
            run("UPDATE profiles SET status='pending' WHERE id=?",(pid,))
            flash("Profile saved. Waiting for admin approval.","ok")
        else: flash("Profile saved.","ok")
        return redirect(url_for("dashboard"))
    return render_template("profile_form.html",p=p,title="Edit Profile")

@app.route("/admin")
@login_required("admin")
def admin_home():
    s=dict(users=count("SELECT COUNT(*) FROM users"),clients=count("SELECT COUNT(*) FROM users WHERE role='client'"),matchmakers=count("SELECT COUNT(*) FROM users WHERE role='matchmaker'"),profiles=count("SELECT COUNT(*) FROM profiles"),pending=count("SELECT COUNT(*) FROM profiles WHERE status='pending'"),approved=count("SELECT COUNT(*) FROM profiles WHERE status='approved'"),rejected=count("SELECT COUNT(*) FROM profiles WHERE status='rejected'"),male=count("SELECT COUNT(*) FROM profiles WHERE gender='Male'"),female=count("SELECT COUNT(*) FROM profiles WHERE gender='Female'"),proposals=count("SELECT COUNT(*) FROM proposals"))
    pstat={st:count("SELECT COUNT(*) FROM proposals WHERE status=?",(st,)) for st in STATUSES}
    recent=q("SELECT * FROM users ORDER BY id DESC LIMIT 6")
    pending=q("SELECT * FROM profiles WHERE status='pending' ORDER BY id DESC LIMIT 6")
    return render_template("admin_home.html",s=s,pstat=pstat,recent=recent,pending=pending)

@app.route("/admin/users")
@login_required("admin")
def admin_users():
    return render_template("admin_users.html",users=q("SELECT * FROM users ORDER BY id DESC"))

@app.post("/admin/users/add")
@login_required("admin")
def admin_add_matchmaker():
    f=request.form
    email=f.get("email","").strip().lower()
    if not f.get("name","").strip() or "@" not in email or len(f.get("password",""))<6:
        flash("Name, valid email and a password of 6+ characters are required.","bad")
    elif q("SELECT 1 FROM users WHERE email=?",(email,),one=True):
        flash("This email already exists.","bad")
    else:
        run("INSERT INTO users(name,email,password,role,phone,created_at) VALUES(?,?,?,?,?,?)",(f["name"].strip(),email,generate_password_hash(f["password"]),"matchmaker",f.get("phone","").strip(),now()))
        flash("Match maker account created.","ok")
    return redirect(url_for("admin_users"))

@app.post("/admin/users/<int:uid>/<act>")
@login_required("admin")
def admin_user_action(uid,act):
    if uid==session["uid"]: flash("You cannot change your own account here.","bad")
    elif act=="toggle": run("UPDATE users SET active = 1 - active WHERE id=?",(uid,))
    elif act=="delete":
        for p in q("SELECT id FROM profiles WHERE user_id=?",(uid,)): delete_profile(p["id"])
        run("UPDATE profiles SET matchmaker_id=NULL WHERE matchmaker_id=?",(uid,))
        run("DELETE FROM users WHERE id=?",(uid,))
        flash("User deleted.","ok")
    return redirect(url_for("admin_users"))

@app.route("/admin/profiles")
@login_required("admin")
def admin_profiles():
    st=request.args.get("status","")
    rows=q("SELECT * FROM profiles WHERE status=? ORDER BY id DESC",(st,)) if st in ("pending","approved","rejected") else q("SELECT * FROM profiles ORDER BY id DESC")
    return render_template("profiles_table.html",rows=rows,st=st,mode="admin",title="All Profiles")

@app.post("/admin/profiles/<int:pid>/<act>")
@login_required("admin")
def admin_profile_action(pid,act):
    if act in ("approve","reject"): run("UPDATE profiles SET status=? WHERE id=?",("approved" if act=="approve" else "rejected",pid))
    elif act=="delete": delete_profile(pid); flash("Profile deleted.","ok")
    return redirect(request.referrer or url_for("admin_profiles"))

@app.route("/admin/proposals")
@login_required("admin")
def admin_proposals():
    rows=q(PROPOSAL_SQL+" ORDER BY pr.id DESC")
    return render_template("proposals.html",rows=rows,mode="admin",title="All Proposals")

@app.route("/matchmaker")
@login_required("matchmaker")
def mm_home():
    uid=session["uid"]
    s=dict(profiles=count("SELECT COUNT(*) FROM profiles WHERE matchmaker_id=?",(uid,)),proposals=count("SELECT COUNT(*) FROM proposals WHERE matchmaker_id=?",(uid,)))
    pstat={st:count("SELECT COUNT(*) FROM proposals WHERE matchmaker_id=? AND status=?",(uid,st)) for st in STATUSES}
    recent=q(PROPOSAL_SQL+" WHERE pr.matchmaker_id=? ORDER BY pr.id DESC LIMIT 6",(uid,))
    return render_template("mm_home.html",s=s,pstat=pstat,recent=recent)

@app.route("/matchmaker/profiles")
@login_required("matchmaker")
def mm_profiles():
    rows=q("SELECT * FROM profiles WHERE matchmaker_id=? ORDER BY id DESC",(session["uid"],))
    return render_template("profiles_table.html",rows=rows,st="",mode="mm",title="My Profiles")

@app.route("/matchmaker/profiles/new", methods=["GET","POST"])
@login_required("matchmaker")
def mm_new_profile():
    if request.method=="POST":
        try: d=form_profile()
        except ValueError as e:
            flash(str(e),"bad")
            return render_template("profile_form.html",p=request.form,title="Add New Profile")
        cols=",".join(PFIELDS)
        run(f"INSERT INTO profiles(matchmaker_id,{cols},status,created_at) VALUES(?,{','.join('?'*len(PFIELDS))},'approved',?)",(session["uid"],*[d[k] for k in PFIELDS],now()))
        flash("Profile added.","ok")
        return redirect(url_for("mm_profiles"))
    return render_template("profile_form.html",p=None,title="Add New Profile")

@app.route("/matchmaker/suggest", methods=["GET","POST"])
@login_required("matchmaker")
def mm_suggest():
    if request.method=="POST":
        a,b=request.form.get("from",type=int),request.form.get("to",type=int)
        if a and b and a!=b and not q("SELECT 1 FROM proposals WHERE (from_profile=? AND to_profile=?) OR (from_profile=? AND to_profile=?)",(a,b,b,a),one=True):
            run("INSERT INTO proposals(from_profile,to_profile,matchmaker_id,kind,status,note,created_at) VALUES(?,?,?,?,?,?,?)",(a,b,session["uid"],"suggestion","pending",request.form.get("note","").strip(),now()))
            flash("Match suggested.","ok")
        else: flash("This pair already exists or is invalid.","bad")
        return redirect(url_for("mm_suggest",pid=a))
    pool=q("SELECT * FROM profiles WHERE status='approved' ORDER BY full_name")
    pid=request.args.get("pid",type=int)
    base,cands=None,[]
    if pid:
        base=q("SELECT * FROM profiles WHERE id=? AND status='approved'",(pid,),one=True)
        if base:
            others=q("SELECT * FROM profiles WHERE status='approved' AND gender<>? AND id<>?",(base["gender"],pid))
            cands=sorted(((score(base,o),o) for o in others),key=lambda t:t[0],reverse=True)
    return render_template("suggest.html",pool=pool,base=base,cands=cands)

@app.route("/matchmaker/proposals")
@login_required("matchmaker")
def mm_proposals():
    rows=q(PROPOSAL_SQL+" WHERE pr.matchmaker_id=? ORDER BY pr.id DESC",(session["uid"],))
    return render_template("proposals.html",rows=rows,mode="mm",title="My Proposals")

@app.post("/proposal/<int:pid>/status")
@login_required("admin","matchmaker")
def proposal_status(pid):
    st=request.form.get("status")
    pr=q("SELECT * FROM proposals WHERE id=?",(pid,),one=True)
    if st not in STATUSES or not pr: abort(400)
    if session["role"]=="matchmaker" and pr["matchmaker_id"]!=session["uid"]: abort(403)
    run("UPDATE proposals SET status=? WHERE id=?",(st,pid))
    return redirect(request.referrer or url_for("dashboard"))

def my_profile(): return q("SELECT * FROM profiles WHERE user_id=?",(session["uid"],),one=True)

@app.route("/client")
@login_required("client")
def client_home():
    me=my_profile()
    s=dict(received=count("SELECT COUNT(*) FROM proposals WHERE to_profile=?",(me["id"],)),waiting=count("SELECT COUNT(*) FROM proposals WHERE to_profile=? AND status='pending'",(me["id"],)),sent=count("SELECT COUNT(*) FROM proposals WHERE from_profile=?",(me["id"],)),accepted=count("SELECT COUNT(*) FROM proposals WHERE (to_profile=? OR from_profile=?) AND status IN ('accepted','married')",(me["id"],me["id"])))
    return render_template("client_home.html",me=me,s=s)

@app.route("/client/browse")
@login_required("client")
def client_browse():
    me=my_profile()
    city=request.args.get("city","").strip()
    amin=request.args.get("min_age",18,type=int)
    amax=request.args.get("max_age",80,type=int)
    rows=q("SELECT * FROM profiles WHERE status='approved' AND gender<>? AND age BETWEEN ? AND ? AND city LIKE ? AND id NOT IN (SELECT to_profile FROM proposals WHERE from_profile=?) AND id NOT IN (SELECT from_profile FROM proposals WHERE to_profile=?) ORDER BY id DESC",(me["gender"],amin,amax,f"%{city}%",me["id"],me["id"]))
    return render_template("browse.html",me=me,rows=rows,city=city,amin=amin,amax=amax)

@app.post("/client/interest/<int:pid>")
@login_required("client")
def client_interest(pid):
    me=my_profile()
    if me["status"]!="approved": flash("Your profile must be approved by the admin first.","bad")
    else:
        run("INSERT INTO proposals(from_profile,to_profile,kind,status,created_at) VALUES(?,?,?,?,?)",(me["id"],pid,"interest","pending",now()))
        flash("Interest sent.","ok")
    return redirect(url_for("client_browse"))

@app.route("/client/proposals")
@login_required("client")
def client_proposals():
    me=my_profile()
    received=q(PROPOSAL_SQL+" WHERE pr.to_profile=? ORDER BY pr.id DESC",(me["id"],))
    sent=q(PROPOSAL_SQL+" WHERE pr.from_profile=? ORDER BY pr.id DESC",(me["id"],))
    return render_template("client_proposals.html",received=received,sent=sent)

@app.post("/client/proposals/<int:pid>/<act>")
@login_required("client")
def client_respond(pid,act):
    me=my_profile()
    pr=q("SELECT * FROM proposals WHERE id=? AND to_profile=?",(pid,me["id"]),one=True)
    if not pr or act not in ("accept","reject"): abort(400)
    run("UPDATE proposals SET status=? WHERE id=?",("accepted" if act=="accept" else "rejected",pid))
    return redirect(url_for("client_proposals"))

TEMPLATES = {}
TEMPLATES["macros.html"] = """{% macro pform(p) %}<div class="fgrid"><label>Full Name<input name="full_name" required value="{{ p.full_name if p else '' }}"></label><label>Gender<select name="gender">{% for o in ['Male','Female'] %}<option {{ 'selected' if p and p.gender==o }}>{{ o }}</option>{% endfor %}</select></label><label>Age<input name="age" type="number" min="18" max="80" required value="{{ p.age if p else '' }}"></label><label>City<input name="city" value="{{ p.city if p else '' }}"></label><label>Religion / Sect<select name="religion">{% for o in RELIGIONS %}<option {{ 'selected' if p and p.religion==o }}>{{ o }}</option>{% endfor %}</select></label><label>Marital Status<select name="marital_status">{% for o in MARITAL %}<option {{ 'selected' if p and p.marital_status==o }}>{{ o }}</option>{% endfor %}</select></label><label>Education<input name="education" value="{{ p.education if p else '' }}"></label><label>Occupation<input name="occupation" value="{{ p.occupation if p else '' }}"></label><label>Height (e.g. 5'8")<input name="height" value="{{ p.height if p else '' }}"></label><label>Phone<input name="phone" value="{{ p.phone if p else '' }}"></label></div><label>About<textarea name="about" rows="3">{{ p.about if p else '' }}</textarea></label><label>Partner Preference<textarea name="partner_pref" rows="3">{{ p.partner_pref if p else '' }}</textarea></label>{% endmacro %}{% macro badge(s) %}<span class="badge {{ s }}">{{ s }}</span>{% endmacro %}{% macro bar(label, value, total) %}<div class="bar"><div class="bl"><span>{{ label }}</span><b>{{ value }}</b></div><div class="bt"><div class="bf" style="width:{{ (value / total * 100) if total else 0 }}%"></div></div></div>{% endmacro %}{% macro stat(label, value) %}<div class="card stat"><b>{{ value }}</b><span>{{ label }}</span></div>{% endmacro %}"""
TEMPLATES["base.html"] = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ app_name }}</title><style>:root{--bg:#0b0f1a;--panel:#121a2b;--acc:#00b4ff;--txt:#e8f1ff;--mut:#7f93b5;--ok:#19d38a;--bad:#ff4d6d;--warn:#ffb020}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font-family:"Segoe UI",Arial,sans-serif}a{color:var(--acc);text-decoration:none}.layout{display:flex;min-height:100vh}.side{width:235px;background:var(--panel);padding:22px 14px;position:sticky;top:0;height:100vh;flex-shrink:0}.logo{font-size:24px;font-weight:900;color:var(--acc)}.role{color:var(--mut);font-size:12px;margin:2px 0 20px;text-transform:uppercase;letter-spacing:2px}.side a{display:block;padding:11px 12px;border-radius:8px;color:var(--txt);font-weight:700;margin-bottom:4px}.side a:hover{background:#0066aa}.main{flex:1;padding:28px;min-width:0}.public{max-width:980px;margin:0 auto;padding:28px}h1{font-size:30px;font-weight:900;margin:0 0 20px}h1 span{color:var(--acc)}h2{font-size:18px;margin:0 0 12px;color:var(--acc)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-bottom:20px}.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px;margin-bottom:20px}.card{background:var(--panel);border:1px solid #1d2b47;border-radius:14px;padding:18px;margin-bottom:14px}.grid .card,.two .card{margin-bottom:0}.stat b{display:block;font-size:36px;color:var(--acc)}.stat span{color:var(--mut);font-weight:600}.bar{margin-bottom:12px}.bl{display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px}.bt{background:#0b0f1a;border-radius:8px;height:10px}.bf{background:var(--acc);height:10px;border-radius:8px}table{width:100%;border-collapse:collapse;font-size:14px}th{background:var(--acc);color:#000;text-align:left;padding:9px}td{padding:9px;border-bottom:1px solid #1d2b47}.tw{overflow-x:auto}.btn,button{background:var(--acc);color:#000;border:0;border-radius:8px;padding:8px 14px;font-weight:800;cursor:pointer;font-size:13px;display:inline-block}.btn:hover,button:hover{filter:brightness(1.15)}.btn.red,button.red{background:var(--bad);color:#fff}.btn.green,button.green{background:var(--ok)}.btn.gray,button.gray{background:#2a3a5c;color:var(--txt)}form.inline{display:inline}input,select,textarea{width:100%;background:#0b0f1a;color:var(--txt);border:1px solid #24365c;border-radius:8px;padding:9px;font-size:14px;margin-top:4px}label{display:block;font-size:13px;color:var(--mut);font-weight:600;margin-bottom:10px}.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0 14px}select.sm{width:auto;padding:5px;margin:0}.badge{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:800;text-transform:uppercase}.badge.pending{background:#3a2b00;color:var(--warn)}.badge.approved,.badge.accepted{background:#003b27;color:var(--ok)}.badge.rejected{background:#40101c;color:var(--bad)}.badge.married{background:#002f4d;color:var(--acc)}.flash{padding:11px 14px;border-radius:10px;margin-bottom:14px;font-weight:700}.flash.ok{background:#003b27;color:var(--ok)}.flash.bad{background:#40101c;color:var(--bad)}.hero{text-align:center;padding:60px 10px}.hero h1{font-size:54px}.hero p{color:var(--mut);font-size:18px}.pc h3{margin:0 0 4px;font-size:18px}.pc p{margin:3px 0;color:var(--mut);font-size:14px}.score{font-weight:900;color:var(--acc)}@media(max-width:760px){.layout{flex-direction:column}.side{width:100%;height:auto;position:static}}</style></head><body>{% if session.uid %}<div class="layout"><div class="side"><div class="logo">💍 {{ app_name }}</div><div class="role">{{ session.role }} panel</div>{% if session.role == 'admin' %}<a href="{{ url_for('admin_home') }}">📊 Dashboard</a><a href="{{ url_for('admin_users') }}">👥 Users</a><a href="{{ url_for('admin_profiles') }}">📝 Profiles</a><a href="{{ url_for('admin_proposals') }}">💌 Proposals</a>{% elif session.role == 'matchmaker' %}<a href="{{ url_for('mm_home') }}">📊 Dashboard</a><a href="{{ url_for('mm_new_profile') }}">➕ Add Profile</a><a href="{{ url_for('mm_profiles') }}">📝 My Profiles</a><a href="{{ url_for('mm_suggest') }}">🤝 Make a Match</a><a href="{{ url_for('mm_proposals') }}">💌 My Proposals</a>{% else %}<a href="{{ url_for('client_home') }}">📊 Dashboard</a><a href="{{ url_for('client_browse') }}">🔍 Find Matches</a><a href="{{ url_for('client_proposals') }}">💌 My Proposals</a>{% endif %}<a href="{{ url_for('logout') }}">🚪 Logout ({{ session.name }})</a></div><div class="main">{% else %}<div class="public">{% endif %}{% for cat, msg in get_flashed_messages(with_categories=true) %}<div class="flash {{ cat }}">{{ msg }}</div>{% endfor %}{% block content %}{% endblock %}</div>{% if session.uid %}</div>{% endif %}</body></html>"""
TEMPLATES["home.html"] = """{% extends "base.html" %}{% block content %}<div class="hero"><h1>💍 <span>{{ app_name }}</span></h1><p>Find the right life partner with trusted match makers.</p><br><a class="btn" href="{{ url_for('register') }}">Create Free Profile</a> <a class="btn gray" href="{{ url_for('login') }}">Login</a></div>{% endblock %}"""
TEMPLATES["login.html"] = """{% extends "base.html" %}{% block content %}<div class="card" style="max-width:420px;margin:40px auto"><h1>🔐 <span>Login</span></h1><form method="post"><label>Email<input name="email" type="email" required></label><label>Password<input name="password" type="password" required></label><button>Login</button> <a href="{{ url_for('register') }}">Create account</a></form></div>{% endblock %}"""
TEMPLATES["register.html"] = """{% extends "base.html" %}{% from "macros.html" import pform with context %}{% block content %}<h1>📝 Create Your <span>Profile</span></h1><form method="post" class="card"><div class="fgrid"><label>Email<input name="email" type="email" required value="{{ p.email if p else '' }}"></label><label>Password (6+)<input name="password" type="password" required></label></div>{{ pform(p) }}<button>Register</button> <a href="{{ url_for('login') }}">Already have an account?</a></form>{% endblock %}"""
TEMPLATES["profile_form.html"] = """{% extends "base.html" %}{% from "macros.html" import pform with context %}{% block content %}<h1>✏️ <span>{{ title }}</span></h1><form method="post" class="card">{{ pform(p) }}<button>Save Profile</button></form>{% endblock %}"""
TEMPLATES["profile_view.html"] = """{% extends "base.html" %}{% from "macros.html" import badge %}{% block content %}<h1>👤 <span>{{ p.full_name }}</span></h1><div class="card pc"><p>{{ p.gender }} • {{ p.age }} years • {{ p.city }} • {{ p.height }}</p><p>🕌 {{ p.religion }} • 💍 {{ p.marital_status }}</p><p>🎓 {{ p.education }} • 💼 {{ p.occupation }}</p><p><b>About:</b> {{ p.about }}</p><p><b>Looking for:</b> {{ p.partner_pref }}</p><p>Status: {{ badge(p.status) }}</p>{% if session.role in ('admin','matchmaker') %}<p>📞 {{ p.phone }}</p>{% endif %}</div>{% endblock %}"""
TEMPLATES["admin_home.html"] = """{% extends "base.html" %}{% from "macros.html" import stat, bar, badge %}{% block content %}<h1>📊 Admin <span>Dashboard</span></h1><div class="grid">{{ stat('Total Users', s.users) }}{{ stat('Clients', s.clients) }}{{ stat('Match Makers', s.matchmakers) }}{{ stat('Profiles', s.profiles) }}{{ stat('Waiting Approval', s.pending) }}{{ stat('Proposals', s.proposals) }}</div><div class="two"><div class="card"><h2>Gender</h2>{{ bar('Male', s.male, s.profiles) }}{{ bar('Female', s.female, s.profiles) }}</div><div class="card"><h2>Profile Status</h2>{{ bar('Pending', s.pending, s.profiles) }}{{ bar('Approved', s.approved, s.profiles) }}{{ bar('Rejected', s.rejected, s.profiles) }}</div><div class="card"><h2>Proposals</h2>{% for k, v in pstat.items() %}{{ bar(k|capitalize, v, s.proposals) }}{% endfor %}</div></div><div class="two"><div class="card"><h2>Profiles waiting for approval</h2>{% for p in pending %}<p>{{ p.full_name }} ({{ p.age }}, {{ p.city }})<form class="inline" method="post" action="{{ url_for('admin_profile_action', pid=p.id, act='approve') }}"><button class="green">Approve</button></form><form class="inline" method="post" action="{{ url_for('admin_profile_action', pid=p.id, act='reject') }}"><button class="red">Reject</button></form></p>{% else %}<p>Nothing pending ✅</p>{% endfor %}</div><div class="card"><h2>Recent users</h2>{% for u in recent %}<p>{{ u.name }} — <small>{{ u.role }}</small></p>{% endfor %}</div></div>{% endblock %}"""
TEMPLATES["admin_users.html"] = """{% extends "base.html" %}{% from "macros.html" import badge %}{% block content %}<h1>👥 <span>Users</span></h1><form method="post" action="{{ url_for('admin_add_matchmaker') }}" class="card"><h2>➕ Add Match Maker</h2><div class="fgrid"><label>Name<input name="name" required></label><label>Email<input name="email" type="email" required></label><label>Phone<input name="phone"></label><label>Password<input name="password" type="password" required></label></div><button>Create Match Maker</button></form><div class="card tw"><table><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Phone</th><th>Account</th><th>Actions</th></tr>{% for u in users %}<tr><td>{{ u.id }}</td><td>{{ u.name }}</td><td>{{ u.email }}</td><td>{{ u.role }}</td><td>{{ u.phone }}</td><td>{{ badge('accepted' if u.active else 'rejected') }}</td><td>{% if u.id != session.uid %}<form class="inline" method="post" action="{{ url_for('admin_user_action', uid=u.id, act='toggle') }}"><button class="gray">{{ 'Disable' if u.active else 'Enable' }}</button></form><form class="inline" method="post" action="{{ url_for('admin_user_action', uid=u.id, act='delete') }}" onsubmit="return confirm('Delete?')"><button class="red">Delete</button></form>{% endif %}</td></tr>{% endfor %}</table></div>{% endblock %}"""
TEMPLATES["profiles_table.html"] = """{% extends "base.html" %}{% from "macros.html" import badge %}{% block content %}<h1>📝 <span>{{ title }}</span></h1>{% if mode == 'admin' %}<p><a class="btn {{ '' if not st else 'gray' }}" href="{{ url_for('admin_profiles') }}">All</a> <a class="btn {{ '' if st=='pending' else 'gray' }}" href="{{ url_for('admin_profiles', status='pending') }}">Pending</a> <a class="btn {{ '' if st=='approved' else 'gray' }}" href="{{ url_for('admin_profiles', status='approved') }}">Approved</a> <a class="btn {{ '' if st=='rejected' else 'gray' }}" href="{{ url_for('admin_profiles', status='rejected') }}">Rejected</a></p>{% endif %}<div class="card tw"><table><tr><th>ID</th><th>Name</th><th>Gender</th><th>Age</th><th>City</th><th>Religion</th><th>Education</th><th>Status</th><th>Actions</th></tr>{% for p in rows %}<tr><td>{{ p.id }}</td><td><a href="{{ url_for('profile_view', pid=p.id) }}">{{ p.full_name }}</a></td><td>{{ p.gender }}</td><td>{{ p.age }}</td><td>{{ p.city }}</td><td>{{ p.religion }}</td><td>{{ p.education }}</td><td>{{ badge(p.status) }}</td><td><a class="btn gray" href="{{ url_for('profile_edit', pid=p.id) }}">Edit</a>{% if mode == 'admin' %}<form class="inline" method="post" action="{{ url_for('admin_profile_action', pid=p.id, act='approve') }}"><button class="green">Approve</button></form><form class="inline" method="post" action="{{ url_for('admin_profile_action', pid=p.id, act='reject') }}"><button class="gray">Reject</button></form><form class="inline" method="post" action="{{ url_for('admin_profile_action', pid=p.id, act='delete') }}" onsubmit="return confirm('Delete?')"><button class="red">Delete</button></form>{% endif %}</td></tr>{% else %}<tr><td colspan="9">No profiles yet.</td></tr>{% endfor %}</table></div>{% endblock %}"""
TEMPLATES["proposals.html"] = """{% extends "base.html" %}{% from "macros.html" import badge %}{% block content %}<h1>💌 <span>{{ title }}</span></h1><div class="card tw"><table><tr><th>ID</th><th>From</th><th>To</th><th>Type</th><th>Match Maker</th><th>Date</th><th>Status</th><th>Change</th></tr>{% for r in rows %}<tr><td>{{ r.id }}</td><td><a href="{{ url_for('profile_view', pid=r.from_profile) }}">{{ r.a_name }}</a> ({{ r.a_age }})</td><td><a href="{{ url_for('profile_view', pid=r.to_profile) }}">{{ r.b_name }}</a> ({{ r.b_age }})</td><td>{{ r.kind }}</td><td>{{ r.mm_name or '-' }}</td><td>{{ r.created_at }}</td><td>{{ badge(r.status) }}</td><td>{% if mode == 'admin' or r.matchmaker_id == session.uid %}<form class="inline" method="post" action="{{ url_for('proposal_status', pid=r.id) }}"><select class="sm" name="status">{% for st in STATUSES %}<option {{ 'selected' if st==r.status }}>{{ st }}</option>{% endfor %}</select><button>Save</button></form>{% endif %}</td></tr>{% else %}<tr><td colspan="8">No proposals yet.</td></tr>{% endfor %}</table></div>{% endblock %}"""
TEMPLATES["mm_home.html"] = """{% extends "base.html" %}{% from "macros.html" import stat, bar, badge %}{% block content %}<h1>📊 Match Maker <span>Dashboard</span></h1><div class="grid">{{ stat('My Profiles', s.profiles) }}{{ stat('My Proposals', s.proposals) }}{{ stat('Accepted', pstat.accepted) }}{{ stat('Married 🎉', pstat.married) }}</div><div class="two"><div class="card"><h2>Proposal Status</h2>{% for k, v in pstat.items() %}{{ bar(k|capitalize, v, s.proposals) }}{% endfor %}</div><div class="card"><h2>Quick Actions</h2><p><a class="btn" href="{{ url_for('mm_new_profile') }}">➕ Add Profile</a></p><p><a class="btn" href="{{ url_for('mm_suggest') }}">🤝 Make a Match</a></p></div></div><div class="card tw"><h2>Recent proposals</h2><table><tr><th>From</th><th>To</th><th>Status</th><th>Date</th></tr>{% for r in recent %}<tr><td>{{ r.a_name }}</td><td>{{ r.b_name }}</td><td>{{ badge(r.status) }}</td><td>{{ r.created_at }}</td></tr>{% else %}<tr><td colspan="4">No proposals yet.</td></tr>{% endfor %}</table></div>{% endblock %}"""
TEMPLATES["suggest.html"] = """{% extends "base.html" %}{% block content %}<h1>🤝 Make a <span>Match</span></h1><form method="get" class="card"><label>Choose a profile to find matches for<select name="pid" onchange="this.form.submit()"><option value="">-- select --</option>{% for p in pool %}<option value="{{ p.id }}" {{ 'selected' if base and base.id==p.id }}>{{ p.full_name }} ({{ p.gender }}, {{ p.age }}, {{ p.city }})</option>{% endfor %}</select></label></form>{% if base %}<div class="card tw"><h2>Best matches for {{ base.full_name }}</h2><table><tr><th>Score</th><th>Name</th><th>Age</th><th>City</th><th>Religion</th><th>Education</th><th>Suggest</th></tr>{% for sc, o in cands %}<tr><td class="score">{{ sc }}%</td><td><a href="{{ url_for('profile_view', pid=o.id) }}">{{ o.full_name }}</a></td><td>{{ o.age }}</td><td>{{ o.city }}</td><td>{{ o.religion }}</td><td>{{ o.education }}</td><td><form class="inline" method="post"><input type="hidden" name="from" value="{{ base.id }}"><input type="hidden" name="to" value="{{ o.id }}"><input name="note" placeholder="Note" style="width:150px"> <button>Suggest</button></form></td></tr>{% else %}<tr><td colspan="7">No approved profiles.</td></tr>{% endfor %}</table></div>{% endif %}{% endblock %}"""
TEMPLATES["client_home.html"] = """{% extends "base.html" %}{% from "macros.html" import stat, badge %}{% block content %}<h1>📊 Welcome, <span>{{ me.full_name }}</span></h1><div class="grid">{{ stat('Proposals Received', s.received) }}{{ stat('Waiting Reply', s.waiting) }}{{ stat('Interests Sent', s.sent) }}{{ stat('Accepted ❤️', s.accepted) }}</div><div class="card pc"><h2>My Profile</h2><p>Status: {{ badge(me.status) }}</p><p>{{ me.gender }} • {{ me.age }} years • {{ me.city }} • {{ me.religion }} • {{ me.marital_status }}</p><p>🎓 {{ me.education }} • 💼 {{ me.occupation }}</p><a class="btn" href="{{ url_for('profile_edit', pid=me.id) }}">✏️ Edit Profile</a> <a class="btn gray" href="{{ url_for('client_browse') }}">🔍 Find Matches</a></div>{% endblock %}"""
TEMPLATES["browse.html"] = """{% extends "base.html" %}{% block content %}<h1>🔍 Find <span>Matches</span></h1><form method="get" class="card"><div class="fgrid"><label>City<input name="city" value="{{ city }}"></label><label>Min Age<input name="min_age" type="number" value="{{ amin }}"></label><label>Max Age<input name="max_age" type="number" value="{{ amax }}"></label></div><button>Search</button></form><div class="grid">{% for p in rows %}<div class="card pc"><h3>{{ p.full_name }}</h3><p>{{ p.age }} years • {{ p.city }} • {{ p.height }}</p><p>🕌 {{ p.religion }} • 💍 {{ p.marital_status }}</p><p>🎓 {{ p.education }}</p><p>💼 {{ p.occupation }}</p><p>{{ p.about }}</p><form method="post" action="{{ url_for('client_interest', pid=p.id) }}"><button>💌 Send Interest</button></form></div>{% else %}<p>No matches found.</p>{% endfor %}</div>{% endblock %}"""
TEMPLATES["client_proposals.html"] = """{% extends "base.html" %}{% from "macros.html" import badge %}{% block content %}<h1>💌 My <span>Proposals</span></h1><div class="card tw"><h2>Received</h2><table><tr><th>From</th><th>Age</th><th>City</th><th>Type</th><th>Status</th><th>Action</th></tr>{% for r in received %}<tr><td><a href="{{ url_for('profile_view', pid=r.from_profile) }}">{{ r.a_name }}</a></td><td>{{ r.a_age }}</td><td>{{ r.a_city }}</td><td>{{ 'Suggested' if r.kind=='suggestion' else 'Interest' }}{% if r.note %}<br><small>{{ r.note }}</small>{% endif %}</td><td>{{ badge(r.status) }}{% if r.status in ('accepted','married') %}<br>📞 {{ r.a_phone }}{% endif %}</td><td>{% if r.status == 'pending' %}<form class="inline" method="post" action="{{ url_for('client_respond', pid=r.id, act='accept') }}"><button class="green">Accept</button></form><form class="inline" method="post" action="{{ url_for('client_respond', pid=r.id, act='reject') }}"><button class="red">Reject</button></form>{% endif %}</td></tr>{% else %}<tr><td colspan="6">Nothing received yet.</td></tr>{% endfor %}</table></div><div class="card tw"><h2>Sent</h2><table><tr><th>To</th><th>Age</th><th>City</th><th>Status</th></tr>{% for r in sent %}<tr><td><a href="{{ url_for('profile_view', pid=r.to_profile) }}">{{ r.b_name }}</a></td><td>{{ r.b_age }}</td><td>{{ r.b_city }}</td><td>{{ badge(r.status) }}{% if r.status in ('accepted','married') %}<br>📞 {{ r.b_phone }}{% endif %}</td></tr>{% else %}<tr><td colspan="4">Nothing sent yet.</td></tr>{% endfor %}</table></div>{% endblock %}"""

app.jinja_loader = DictLoader(TEMPLATES)

if __name__ == "__main__":
    init_db()
    print(f"\n  {APP_NAME} is running -> http://127.0.0.1:5000")
    print(f"  Admin login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}\n")
    app.run(debug=True, use_reloader=False)