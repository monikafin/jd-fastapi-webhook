from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import httpx
import os
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

ZOHO_WEBHOOK_URL = os.getenv("ZOHO_WEBHOOK_URL")

if not ZOHO_WEBHOOK_URL:
    raise Exception("ZOHO_WEBHOOK_URL missing in .env")

app = FastAPI()

# -----------------------------
# OPTIONAL: JD IP WHITELIST
# -----------------------------
ALLOWED_IPS = [
    "103.20.126.250",
    "103.20.127.26",
    "103.20.126.4"
]

# -----------------------------
# JD Webhook Endpoint
# -----------------------------
@app.api_route("/jd-webhook", methods=["GET", "POST"])
async def receive_jd_webhook(request: Request):

    # =============================
    # 🛡️ STEP 1: IP VALIDATION (OPTIONAL)
    # =============================
    client_ip = request.client.host

    if client_ip not in ALLOWED_IPS:
        return PlainTextResponse("FAILED", status_code=403)

    # =============================
    # 🔹 STEP 2: READ JD DATA
    # =============================
    data = {}

    # Handle GET request
    if request.method == "GET":
        data = dict(request.query_params)

    # Handle POST request
    else:
        try:
            # Try JSON
            data = await request.json()
            if not isinstance(data, dict):
                data = {}
        except:
            # Fallback to form-data
            form = await request.form()
            data = dict(form)

    # =============================
    # 🛡️ STEP 3: VALIDATE REQUIRED FIELD
    # =============================
    if not data.get("leadid") or not data.get("mobile"):
        return PlainTextResponse("FAILED", status_code=400)

    # =============================
    # 🧹 STEP 4: KEEP ONLY JD FIELDS
    # =============================
    allowed_fields = {
        "leadid","leadtype","prefix","name","mobile","phone","email",
        "date","category","city","area","brancharea","dncmobile",
        "dncphone","company","pincode","time","branchpin","parentid"
    }

    cleaned_data = {k: v for k, v in data.items() if k in allowed_fields}

    # =============================
    # 🚀 STEP 5: FORWARD TO ZOHO
    # =============================
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                ZOHO_WEBHOOK_URL,
                params=cleaned_data   # Zoho expects params
            )
    except Exception as e:
        return PlainTextResponse("FAILED", status_code=500)

    # =============================
    # ✅ STEP 6: JD REQUIRED RESPONSE
    # =============================
    return PlainTextResponse("SUCCESS")