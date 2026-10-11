from flask import Flask, request, session, redirect, url_for, send_file, render_template_string
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from urllib.parse import urlparse
import os, requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-public-hosting")
app.config["MAX_CONTENT_LENGTH"] = 26 * 1024 * 1024
MAX_BYTES = 25 * 1024 * 1024

QUESTIONS = [
("Who is Namit's best friend?", ["Pranet Gada","Vidhit luniya","Yash Nahar","Namit's mumma"], 3),
("What is Namit's favourite food snack?", ["Pizza","French fries","Burger","Cheese sandwich"], 1),
("What does Namit dislike the most about people?", ["Lie & slyness","Lie & faking personality","Slyness & faking personality","Back bitching & slyness"], 2),
("Which skill is Namit longing to pursue?", ["Stock market analysis & coding","Coding & video editing","Video editing & stock market analysis","Making a robot & coding"], 3),
("Which place is on Namit's bucket list?", ["Switzerland, Italy & New Zealand","Singapore, Japan & USA","Switzerland, Japan & Spain","Australia, New Zealand & Switzerland"], 3),
("When life gets mean, who does Namit go back to?", ["Vidhit","Mumma","Sister","Self healer"], 2),
]
# Hidden code: Q1=0001, Q2=0010, Q3=0011, Q4=0100, Q5=0101, Q6=0110.
UNLOCK_CODE = "000100100011010001010110"

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Namit PDF Locker</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:18px;min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#101828,#344054);font-family:Arial,sans-serif}
.card{background:#fff;width:min(720px,100%);padding:26px;border-radius:20px;box-shadow:0 20px 60px #0005}h1{text-align:center;margin:0 0 8px;color:#101828}.muted{text-align:center;color:#667085;margin:0 0 22px}
fieldset{border:1px solid #d0d5dd;border-radius:12px;margin:14px 0;padding:14px}legend{font-weight:bold;padding:0 6px}.opt{display:block;padding:7px 0;color:#101828}
input[type=text],input[type=password],input[type=url],input[type=file]{display:block;width:100%;padding:12px;border:1px solid #d0d5dd;border-radius:9px;font-size:16px;margin:8px 0 16px}
label.head{font-weight:bold;display:block;margin-top:14px}button{width:100%;padding:14px;border:0;border-radius:10px;background:#111827;color:white;font-weight:bold;font-size:16px;cursor:pointer;margin-top:12px}.error{background:#fef3f2;color:#b42318;padding:12px;border-radius:9px}.note{font-size:13px;line-height:1.5;color:#667085}
</style></head><body><main class="card"><h1>🔐 Namit PDF Locker</h1><p class="muted">Answer the quiz to unlock PDF protection.</p>
{% if error %}<p class="error">{{error}}</p>{% endif %}
{% if step == 1 %}
<form method="post" action="/quiz">

{% for q in questions %}
{% set qnum = loop.index %}
<fieldset>
  <legend>Q{{ qnum }}. {{ q[0] }}</legend>
  {% for op in q[1] %}
  <label class="opt">
    <input type="radio" name="q{{ qnum }}" value="{{ loop.index0 }}" required>
    {{ ["a","b","c","d"][loop.index0] }}) {{ op }}
  </label>
  {% endfor %}
</fieldset>
{% endfor %}

{% elif step == 2 %}
<p>All six answers are correct. Enter the binary unlock code.</p><form method="post" action="/code"><label class="head">Binary unlock code</label><input type="text" name="code" pattern="[01]+" inputmode="numeric" required placeholder="Enter binary code"><button>Unlock PDF Locker</button></form>
{% else %}
<p>Upload a PDF or paste a direct public PDF link. Choose a password to protect the downloaded copy.</p>
<form method="post" action="/lock" enctype="multipart/form-data">
<label class="head">PDF from your device (optional)</label><input type="file" name="pdf" accept=".pdf,application/pdf">
<label class="head">Or direct PDF link</label><input type="url" name="pdf_url" placeholder="https://example.com/document.pdf">
<label class="head">Password for the locked PDF</label><input type="password" name="password" required autocomplete="new-password">
<button>Lock PDF & Download</button></form>
<p class="note">The answer key and unlock code are not displayed. PDFs are processed temporarily by the server. Do not use a third-party hosted version for confidential files unless you trust the host.</p>
{% endif %}<p class="note">Maximum PDF size: 25 MB. Links must point directly to a publicly accessible PDF file.</p></main></body></html>"""

def render(step, error=None):
    return render_template_string(HTML, step=step, questions=QUESTIONS, error=error)

@app.get("/")
def home():
    session.clear()
    return render(1)

@app.post("/quiz")
def quiz():
    for i, q in enumerate(QUESTIONS, 1):
        val = request.form.get(f"q{i}", "")
        if not val.isdigit() or int(val) != q[2]:
            session.clear()
            return render(1, "One or more answers are incorrect. Please try all six again."), 400
    session["quiz_ok"] = True
    return render(2)

@app.post("/code")
def code():
    if not session.get("quiz_ok"):
        return redirect(url_for("home"))
    if request.form.get("code", "").strip() != UNLOCK_CODE:
        return render(2, "Incorrect binary code. Please try again."), 400
    session["code_ok"] = True
    return render(3)

@app.post("/lock")
def lock():
    if not session.get("quiz_ok") or not session.get("code_ok"):
        return redirect(url_for("home"))
    password = request.form.get("password", "")
    upload = request.files.get("pdf")
    link = request.form.get("pdf_url", "").strip()
    if not password:
        return render(3, "Enter a password."), 400
    try:
        if upload and upload.filename:
            raw = upload.read(MAX_BYTES + 1)
            filename = os.path.basename(upload.filename)
        elif link:
            parsed = urlparse(link)
            if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.hostname in ("localhost", "127.0.0.1"):
                return render(3, "Enter a valid public direct PDF URL."), 400
            with requests.get(link, stream=True, timeout=20, allow_redirects=False) as r:
                r.raise_for_status()
                chunks, size = [], 0
                for chunk in r.iter_content(65536):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        return render(3, "PDF exceeds 25 MB."), 413
                    chunks.append(chunk)
                raw = b"".join(chunks)
            filename = os.path.basename(parsed.path) or "document.pdf"
        else:
            return render(3, "Choose a PDF or paste a direct PDF link."), 400
        if len(raw) > MAX_BYTES:
            return render(3, "PDF exceeds 25 MB."), 413
        if not raw.startswith(b"%PDF"):
            return render(3, "That file/link does not look like a PDF."), 400
        reader = PdfReader(BytesIO(raw))
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        writer.encrypt(password)
        out = BytesIO()
        writer.write(out)
        out.seek(0)
        base = filename[:-4] if filename.lower().endswith(".pdf") else filename
        return send_file(out, mimetype="application/pdf", as_attachment=True, download_name=(base or "document") + "_locked.pdf")
    except Exception:
        return render(3, "Could not lock this PDF. Make sure the link points directly to a reachable PDF."), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
