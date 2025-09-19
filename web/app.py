
import os, uuid, datetime, psycopg2, jwt, re
from flask import Flask, request, render_template, make_response, jsonify
from flask_socketio import SocketIO, emit

def db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

START_QUEUE = 499_999  # initial baseline

def create_app():
    app = Flask(__name__, static_url_path="/static")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "change-me")
    sio = SocketIO(app, async_mode="eventlet")

    ### helpers ###
    def schema_name(u): return f"kiasu_{u.replace('-', '')}"

    def ensure_schema(u):
        sc = schema_name(u)
        conn = db()
        cur = conn.cursor()
        # schema owned by postgres; ctf_user only gains USAGE
        cur.execute(f"""DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = '{sc}') THEN
            EXECUTE 'CREATE SCHEMA {sc} AUTHORIZATION CURRENT_ROLE';
            EXECUTE 'GRANT USAGE ON SCHEMA {sc} TO ctf_user';
          END IF;
        END$$;""")
        conn.commit(); cur.close(); conn.close()

    def init_queue(u):
        conn, sc = db(), schema_name(u)
        cur = conn.cursor()
        cur.execute(f"SET search_path TO {sc}")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS queue_positions(
              user_uuid TEXT PRIMARY KEY,
              position INTEGER,
              created_at TIMESTAMP
            );
        """)
        # position = max+1 or baseline+1
        cur.execute("SELECT COALESCE(MAX(position), %s) + 1 FROM queue_positions", (START_QUEUE,))
        next_pos = cur.fetchone()[0]
        cur.execute("INSERT INTO queue_positions(user_uuid, position, created_at) VALUES(%s,%s,NOW()) ON CONFLICT (user_uuid) DO NOTHING", (u, next_pos))
        conn.commit(); cur.close(); conn.close()
        broadcast_queue_size()

    def get_position(u):
        conn, sc = db(), schema_name(u); cur = conn.cursor()
        cur.execute(f"SET search_path TO {sc}")
        cur.execute("SELECT position FROM queue_positions WHERE user_uuid=%s", (u,))
        pos = cur.fetchone()[0]; cur.close(); conn.close(); return pos

    def max_queue():
        conn = db()
        cur = conn.cursor()
        # search through pg_namespace for queue tables
        cur.execute("""
        SELECT MAX(position) FROM (
          SELECT MAX(position) AS position FROM (
            SELECT nspname FROM pg_namespace WHERE nspname LIKE 'kiasu_%'
          ) s
          JOIN LATERAL (
            SELECT position FROM pg_catalog.pg_tables t WHERE tablename='queue_positions'
          ) q ON TRUE
        ) x;
        """)  # fallback
        cur.execute("SELECT COALESCE(MAX(position), %s) FROM public.audit_log", (START_QUEUE,))
        result = cur.fetchone()[0] or START_QUEUE
        cur.close(); conn.close(); return result

    def broadcast_queue_size():
        sio.emit("queue-size", {"max": max_queue()})

    ### routes ###
    @app.route("/")
    def index():
        user_uuid = request.cookies.get("user_uuid")
        if not user_uuid:
            user_uuid = str(uuid.uuid4())
            ensure_schema(user_uuid)
            init_queue(user_uuid)
        resp = make_response(render_template("index.html", max_queue=max_queue()))
        resp.set_cookie("user_uuid", user_uuid, max_age=60*60*24, secure=False, httponly=True, samesite="Lax")
        return resp

    @app.route("/queue-position")
    def queue_position():
        u = request.cookies.get("user_uuid")
        if not u: return jsonify({"error":"no uuid"}), 400
        return jsonify({"position": get_position(u)})

    @app.route("/admin-kiasu-interface", methods=["GET","POST"])
    def admin_login():
        query, result = "", ""
        if request.method == "POST":
            query = request.form.get("username","")
            u = request.cookies.get("user_uuid")
            try:
                conn, sc = db(), schema_name(u); cur = conn.cursor()
                cur.execute(f"SET search_path TO {sc}")
                cur.execute(query)  # the vuln
                if cur.description: result = str(cur.fetchall())
                else: result = "Query OK"
                conn.commit(); cur.close(); conn.close()
            except Exception as e:
                # sanitise error message to keep page alive
                result = f"ERROR: {re.sub('[\r\n]+',' ', str(e))}"
        return render_template("admin.html", query=query, result=result)

    @app.route("/admin-dashboard")
    def admin_dash():
        token = request.cookies.get("session","")
        try:
            payload = jwt.decode(token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
            if payload.get("user") == "admin":
                return render_template("dashboard.html", flag="flag{G1tHub_0S1NT_R3v3al}")
        except jwt.InvalidTokenError:
            pass
        return "Forbidden", 403

    ### socket.io ###
    @sio.on("join")
    def on_join():
        emit("queue-size", {"max": max_queue()})
        u = request.cookies.get("user_uuid")
        if u:
            emit("position-update", {"pos": get_position(u)})

    return app

app = create_app()
