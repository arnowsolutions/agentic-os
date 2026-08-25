#!/usr/bin/env python3
"""Upload a PDF to FormForge and make it a fillable public form.
Usage: python3 formforge_upload.py <local.pdf> [label]
Creates the doc under Shareef's user, runs detect+generate, prints a public URL.
"""
import base64, hashlib, json, os, subprocess, sys, uuid, urllib.request

VPS = "147.93.113.241"
TARGET = sys.argv[1] if len(sys.argv) > 1 else ""
LABEL = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(TARGET)
if not TARGET:
    raise SystemExit("usage: formforge_upload.py <local.pdf> [label]")

USER_ID = "284841b2-f2dd-4a38-a3a4-c5d2fb0d41b9"  # Shareef

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.stdout.strip()

def vps(cmd):
    return sh(["ssh", "-o", "StrictHostKeyChecking=no", f"root@{VPS}", cmd])

# Remote-run a python snippet that does storage+db+service calls on the VPS.
with open(TARGET, "rb") as f:
    pdf_b64 = base64.b64encode(f.read()).decode()

storage_ip = vps("docker inspect supabase-storage -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'").strip()
anon = vps("cat /root/scripts/.anon-jwt").strip()

remote_script = '''
import base64, json, os, sys, uuid, urllib.request, urllib.parse
pdf_b64 = sys.stdin.read()
pdf_bytes = base64.b64decode(pdf_b64.strip())
storage_ip = "__STORAGE_IP__"
anon = "__ANON__"
user_id = "__USER_ID__"
label = "__LABEL__"

random_object = str(uuid.uuid4())
path = "__USER_ID__/" + random_object + ".pdf"
# 1. upload to storage container (pdfs bucket, private)
req = urllib.request.Request(
    "http://__STORAGE_IP__:5000/object/pdfs/" + path,
    data=pdf_bytes, method="PUT",
    headers={"Content-Type": "application/pdf"})
urllib.request.urlopen(req, timeout=60).read()

# 2. insert pdf_documents row
body = json.dumps({
    "user_id": user_id, "filename": label, "original_filename": label,
    "page_count": 1, "status": "uploading", "storage_path": path, "published": False
}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8001/rest/v1/pdf_documents",
    data=body, method="POST",
    headers={"Content-Type": "application/json", "apikey": anon, "Authorization": "Bearer " + anon})
doc = json.loads(urllib.request.urlopen(req, timeout=30).read())
doc_id = doc[0]["id"] if isinstance(doc, list) else doc["id"]
print("DOC_ID=" + doc_id, flush=True)

def call_service(ep, payload):
    req = urllib.request.Request("http://127.0.0.1:5099" + ep, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

try:
    d = call_service("/detect", {"documentId": doc_id})
    print("DETECT=" + json.dumps({k: d.get(k) for k in ("fieldsDetected", "detectionMethod", "warning")}), flush=True)
except Exception as e:
    print("DETECT_ERR=" + str(e), flush=True)
try:
    g = call_service("/generate", {"documentId": doc_id, "mode": "overlay"})
    print("GEN=" + json.dumps(g)[:200], flush=True)
except Exception as e:
    print("GEN_ERR=" + str(e), flush=True)
print("STORAGE_PATH=" + path, flush=True)
'''
remote_script = remote_script.replace("__STORAGE_IP__", storage_ip) \
                             .replace("__ANON__", anon) \
                             .replace("__USER_ID__", USER_ID) \
                             .replace("__LABEL__", LABEL)

# Write helper to local temp, scp to VPS, run with PDF on stdin.
import tempfile
local = os.path.join(tempfile.gettempdir(), "formforge_upload_helper.py")
with open(local, "w") as f:
    f.write(remote_script)
subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", local, f"root@{VPS}:/tmp/formforge_upload_helper.py"],
               capture_output=True, timeout=60)
proc2 = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", f"root@{VPS}", "python3 /tmp/formforge_upload_helper.py"],
    input=pdf_b64, capture_output=True, text=True, timeout=400)
sys.stdout.write(proc2.stdout)
if proc2.stderr:
    sys.stderr.write(proc2.stderr[-2000:])
subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"root@{VPS}", "rm -f /tmp/formforge_upload_helper.py"],
               capture_output=True, timeout=30)
