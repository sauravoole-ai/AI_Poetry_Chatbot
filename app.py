from flask import Flask, render_template, request, jsonify, session, send_file
from groq import Groq
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- APP ----------------
app = Flask(__name__)

# ✅ FIX 1: SAFE SECRET KEY (Render-safe fallback)
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret_key_change_me_123")

# ---------------- GROQ ----------------
# ✅ FIX 2: fail-safe API key handling
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in environment variables")

client = Groq(api_key=GROQ_API_KEY)

# ---------------- RASA ----------------
RASA = {
    "Bhakti": "deep devotional love and surrender",
    "Shanta": "peaceful meditative serenity",
    "Karuna": "compassion and tenderness",
    "Veer": "strength, courage and nobility",
    "Adbhuta": "wonder and divine astonishment"
}

# ---------------- SESSION ----------------
@app.before_request
def init_session():
    session.setdefault("rasa", "Bhakti")
    session.setdefault("poem", "")

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- SET RASA ----------------
@app.route("/set_rasa", methods=["POST"])
def set_rasa():
    data = request.get_json(force=True)
    session["rasa"] = data.get("rasa", "Bhakti")
    return jsonify(ok=True)

# ---------------- GENERATE ----------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    topic = data.get("topic", "Krishna")
    rasa = session.get("rasa", "Bhakti")

    prompt = f"""
You are an enlightened devotional poet rooted in Indian spiritual aesthetics.

Write a serene and elevated English poem.

Topic:
{topic}

Mood:
{RASA.get(rasa, "devotional emotion")}

Requirements:
- spiritually uplifting
- emotionally graceful
- vivid sacred imagery
- poetic but readable
- elegant English
- 10 to 16 lines
- no darkness
- no vulgarity
- no modern slang
- calming and divine atmosphere
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=500,
            top_p=1
        )

        poem = response.choices[0].message.content.strip()
        session["poem"] = poem

        return jsonify({"poem": poem})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- PDF ----------------
@app.route("/pdf")
def pdf():
    poem = session.get("poem", "No poem generated yet.")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = [
        Paragraph(poem.replace("\n", "<br/>"), styles["Normal"])
    ]

    doc.build(content)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="divine_poem.pdf",
        mimetype="application/pdf"
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)