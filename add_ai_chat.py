from pathlib import Path

p = Path("master_agent/web.py")
s = p.read_text()

backup = Path("master_agent/web.py.before_ai_chat")
if not backup.exists():
    backup.write_text(s)

imp = "from master_agent.providers.ai_engine import ask_openai, ask_claude"
if imp not in s:
    s = s.replace("import secrets", "import secrets\n" + imp, 1)

if '@app.route("/ai-chat"' in s:
    print("AI CHAT ROUTE ALREADY EXISTS")
else:
    route = r'''
@app.route("/ai-chat", methods=["GET", "POST"])
def ai_chat():
    answer = ""
    error = ""
    question = ""
    provider = "openai"

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        provider = request.form.get("provider", "openai").strip().lower()

        if not question:
            error = "Pehle apna sawal likhiye."
        elif len(question) > 8000:
            error = "Sawal 8000 characters se chhota rakhein."
        elif provider not in ("openai", "claude"):
            error = "Invalid AI provider."
        else:
            result = ask_openai(question) if provider == "openai" else ask_claude(question)
            if result.get("ok"):
                answer = result.get("text", "")
            else:
                error = result.get("error", "AI request failed.")

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="hi">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="{{ url_for('static', filename='premium.css') }}">
      <title>ApnaCare AI Chat</title>
      <style>
        body{background:#07111f;color:#f5f5f5;font-family:Arial;margin:0;padding:18px}
        .chat{max-width:760px;margin:25px auto;background:#101d30;padding:22px;border:1px solid #b99545;border-radius:16px}
        h2{color:#e0bd68}
        textarea,select{box-sizing:border-box;width:100%;padding:13px;margin:10px 0;background:#07111f;color:white;border:1px solid #596579;border-radius:9px}
        button{background:#c6a04b;color:#101827;padding:13px 20px;border:0;border-radius:9px;font-weight:bold}
        .answer,.error{white-space:pre-wrap;padding:14px;margin-top:18px;border-radius:9px;overflow-wrap:anywhere}
        .answer{background:#172b3d;border:1px solid #c6a04b}
        .error{background:#3a2025;color:#ffd5d5}
        a{color:#e0bd68}
      </style>
    </head>
    <body>
      <div class="chat">
        <h2>ApnaCare AI Master Chat</h2>
        <p>Apne business ke sawal AI se poochhiye.</p>
        <form method="POST">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <label>AI Provider</label>
          <select name="provider">
            <option value="openai" {% if provider == 'openai' %}selected{% endif %}>OpenAI</option>
            <option value="claude" {% if provider == 'claude' %}selected{% endif %}>Claude</option>
          </select>
          <label>Aapka sawal</label>
          <textarea name="question" rows="5" maxlength="8000" placeholder="Apna sawal yahan likhein..." required>{{ question }}</textarea>
          <button type="submit">AI se jawab lein</button>
        </form>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if answer %}<div class="answer"><b>AI Response:</b><br><br>{{ answer }}</div>{% endif %}
        <p><a href="/">Dashboard par wapas jaayein</a></p>
        <small>AI responses may be inaccurate. External actions are not executed from this chat.</small>
      </div>
    </body>
    </html>
    """, answer=answer, error=error, question=question, provider=provider)

'''
    anchor = 'if __name__ == "__main__":'
    if anchor not in s:
        raise SystemExit("Main block not found. Original file unchanged.")
    s = s.replace(anchor, route + "\n" + anchor, 1)

p.write_text(s)
print("AI CHAT ROUTE ADDED")
