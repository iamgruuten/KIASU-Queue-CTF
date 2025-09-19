from flask import Flask, request, render_template, make_response, redirect
import os, uuid, psycopg2, jwt
from datetime import datetime, timedelta

app = Flask(__name__)
SECRET = os.getenv("JWT_SECRET_KEY", "kiasu_rs256_secr3t!@#")
DB_URL = os.getenv("DATABASE_URL", "postgresql://ctf_user:insecure@db/kiasu")

def get_conn(schema=None):
    conn = psycopg2.connect(DB_URL)
    if schema:
        cur = conn.cursor()
        cur.execute(f"SET search_path TO {schema};")
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/join")
def join():
    user_uuid = str(uuid.uuid4())
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(position),0)+1 FROM queue_positions;")
    position = cur.fetchone()[0]
    cur.execute("INSERT INTO queue_positions (user_uuid, position) VALUES (%s,%s)", (user_uuid, position))
    conn.commit()

    token = jwt.encode(
        {"user": "guest", "uuid": user_uuid, "exp": datetime.utcnow() + timedelta(hours=1)},
        SECRET,
        algorithm="HS256"
    )

    resp = make_response(render_template("joined.html", position=position))
    resp.set_cookie("user_id", user_uuid, httponly=True, samesite="Lax")
    resp.set_cookie("session", token, httponly=True, samesite="Lax")
    return resp

@app.route("/admin-kiasu-interface", methods=["GET", "POST"])
def admin_interface():
    query = result = None
    if request.method == "POST":
        user_uuid = request.cookies.get("user_id")
        q = request.form.get("username", "")
        query = q
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(q)
            result = str(cur.fetchall()) if cur.description else "Query OK"
            conn.commit()
        except Exception as e:
            result = f"ERROR: {e}"
    return render_template("admin.html", query=query, result=result)

@app.route("/admin-dashboard")
def admin_dash():
    token = request.cookies.get("session")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        if payload.get("user") == "admin":
            return render_template("dashboard.html", flag="flag{G1tHub_0S1NT_R3v3al}")
    except Exception:
        pass
    return "Forbidden!", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
