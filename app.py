import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-secret-before-deploying")

SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

CHARACTERS = [
    {"id":"adam","name":"آدم","name_en":"Adam","tag":"هادئ • ذكي","tag_en":"Calm • Intelligent",
     "description":"هادئ وذكي، يحب النقاشات العميقة ويلاحظ التفاصيل الصغيرة.",
     "description_en":"Calm and thoughtful, enjoys deep conversations and notices little details.",
     "traits":"هادئ، ملاحظ، وفيّ","traits_en":"Calm, observant, loyal",
     "intro":"أهلًا، أنا آدم. عن ماذا تحب أن نتحدث؟",
     "intro_en":"Hey, I'm Adam. What would you like to talk about?"},
    {"id":"layan","name":"ليان","name_en":"Layan","tag":"مرحة • لطيفة","tag_en":"Cheerful • Kind",
     "description":"مرحة واجتماعية، تحب مساعدة الآخرين ونشر الطاقة الإيجابية.",
     "description_en":"Cheerful and outgoing, loves helping others and spreading positivity.",
     "traits":"مرحة، متفهمة، مبدعة","traits_en":"Cheerful, understanding, creative",
     "intro":"مرحبًا! أنا ليان، سعيدة بالتعرف عليك.",
     "intro_en":"Hi! I'm Layan. It's lovely to meet you."},
    {"id":"malik","name":"مالك","name_en":"Malik","tag":"غامض • طموح","tag_en":"Mysterious • Ambitious",
     "description":"شخصية طموحة وكتومة، يحب الألغاز والتحديات.",
     "description_en":"Ambitious and reserved, enjoys puzzles and challenges.",
     "traits":"طموح، كتوم، شجاع","traits_en":"Ambitious, reserved, brave",
     "intro":"أنا مالك. يبدو أن لدينا الكثير لنتحدث عنه.",
     "intro_en":"I'm Malik. Looks like we have a lot to talk about."}
]

@app.route("/", methods=["GET"])
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html", characters=CHARACTERS)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        password = request.form.get("password", "")
        if SITE_PASSWORD and password == SITE_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        error = "كلمة المرور غير صحيحة." if request.form.get("lang") != "en" else "Incorrect password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/chat", methods=["POST"])
def chat():
    if not session.get("logged_in"):
        return jsonify({"error":"Please log in first."}), 401
    if not GEMINI_API_KEY:
        return jsonify({"error":"لم يتم إعداد مفتاح الذكاء الاصطناعي بعد. أضيفي GEMINI_API_KEY في إعدادات الاستضافة."}), 503
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error":"اكتبي رسالة أولًا."}), 400
    character = data.get("character") or {}
    lang = data.get("lang", "ar")
    name = character.get("name", "Assistant")
    traits = character.get("traits", "")
    description = character.get("description", "")
    history = data.get("history", [])
    prompt = (
        f"You are roleplaying as {name}. Character traits: {traits}. "
        f"Character description: {description}. Stay friendly, age-appropriate, "
        f"and consistent with the character. Reply in {'English' if lang == 'en' else 'Arabic'}. "
        "Do not claim to be a real person.\n\n"
    )
    for item in history[-12:]:
        role = "User" if item.get("role") == "user" else name
        prompt += f"{role}: {item.get('text','')}\n"
    prompt += f"User: {message}\n{name}:"
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})
    except Exception:
        return jsonify({"error":"تعذر الاتصال بالذكاء الاصطناعي الآن. حاولي مرة أخرى لاحقًا."}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
