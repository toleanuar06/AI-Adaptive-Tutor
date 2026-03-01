from flask import Flask, render_template, request, jsonify
import subprocess
import json
from google import genai

app = Flask(__name__)

# ЖАСАНДЫ ИНТЕЛЛЕКТ БАПТАУЛАРЫ
API_KEY = "AIzaSyAK8NaoLOmhwqRWcS0NiPYXGmNCMkdlZTI"
client = genai.Client(api_key=API_KEY)

# Оқушының статистикасы (әзірге қарапайым түрде)
user_data = {
    "topic": "Кіріспе (Шығару операторлары)",
    "level": 10,
    "score": 100
}


@app.route('/')
def home():
    return render_template('index.html')


# 1-API: AI-ДАН ТАПСЫРМА СҰРАУ (Жаңартылған)
@app.route('/get_task', methods=['POST'])
def get_task():
    data = request.json
    topic = data.get('topic', 'Кіріспе')  # Фронтендтен тақырыпты қабылдап аламыз
    level = data.get('level', 10)

    prompt = f"""
    Сен C++ ұстазысың. Маған '{topic}' тақырыбы бойынша 1 оңай есеп ойлап тап. Ол 1-2 жолмен жазылатын болсын.
    Оқушының деңгейі: {level}%.
    Жауапты тек JSON форматта қайтар: {{"desc": "Есептің шарты (қазақша)", "hint": "Көмек"}}
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()

        task_info = json.loads(text)
        return jsonify(task_info)
    except Exception as e:
        return jsonify({"desc": f"Қате шықты. Мынаны жазыңыз: std::cout << 'Test';", "hint": "std::cout << 'Test';"})


# 2-API: КОДТЫ КОМПИЛЯЦИЯЛАУ ЖӘНЕ ЛОГИКАЛЫҚ ТЕКСЕРУ
@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '')
    task_desc = data.get('task_desc', '')

    # Кодты C++ файлына сақтап, іске қосу
    with open("temp_code.cpp", "w", encoding="utf-8") as f:
        f.write(f"#include <iostream>\nusing namespace std;\nint main() {{\n{code}\nreturn 0;\n}}")

    try:
        # 1-ҚАДАМ: СИНТАКСИСТІ ТЕКСЕРУ
        compile_process = subprocess.run(["g++", "temp_code.cpp", "-o", "temp_run.exe"], capture_output=True, text=True,
                                         encoding="utf-8", errors="replace")

        if compile_process.returncode != 0:
            err = compile_process.stderr.split("temp_code.cpp")[
                1] if "temp_code.cpp" in compile_process.stderr else compile_process.stderr
            ai_prompt = f"Тапсырма: {task_desc}. Код: {code}. Қате: {err[:300]}. Қатені қазақша түсіндір (2 сөйлем)."
            ai_response = client.models.generate_content(model='gemini-2.5-flash', contents=ai_prompt).text

            user_data["level"] = max(0, user_data["level"] - 10)
            return jsonify(
                {"status": "error", "message": f"[СИНТАКСИС ҚАТЕСІ]: {ai_response}", "level": user_data["level"]})

        # 2-ҚАДАМ: КОДТЫ НАҚТЫ ОРЫНДАУ ЖӘНЕ НӘТИЖЕСІН АЛУ (ОСЫ ЖЕРГЕ UTF-8 ҚОСЫЛДЫ)
        run_process = subprocess.run(["temp_run.exe"], capture_output=True, text=True, encoding="utf-8",
                                     errors="replace", timeout=3)
        actual_output = run_process.stdout.strip()

        # 3-ҚАДАМ: AI АРҚЫЛЫ ЛОГИКАНЫ ТЕКСЕРУ
        eval_prompt = f"""
        Сен қатаң бағдарламалау ұстазысың.
        Тапсырма: "{task_desc}"
        Оқушы жазған код: "{code}"
        Бағдарламаның экранға шығарған нақты жауабы: "{actual_output}"

        Оқушы тапсырманы ТОЛЫҚ әрі ДҰРЫС орындады ма? (Мысалы, тапсырмадағы сөздер дәл солай шықты ма, жаңа жолға өтті ме?)
        Егер 100% дұрыс болса, тек қана "YES" деп жаз. 
        Егер қате болса, "NO|" деп бастап, қатені 1 сөйлеммен қазақша түсіндір.
        """
        eval_response = client.models.generate_content(model='gemini-2.5-flash', contents=eval_prompt).text.strip()

        # НӘТИЖЕНІ САРАПТАУ
        if eval_response.startswith("YES"):
            user_data["level"] = min(100, user_data["level"] + 30)
            return jsonify(
                {"status": "success", "message": f"[ТАМАША]: Код дұрыс жұмыс істеді! Нәтиже: {actual_output}",
                 "level": user_data["level"]})
        else:
            feedback = eval_response.replace("NO|", "").replace("NO", "").strip()
            user_data["level"] = max(0, user_data["level"] - 10)
            return jsonify({"status": "error",
                            "message": f"[ЛОГИКАЛЫҚ ҚАТЕ]: {feedback}<br><br><i>Сіздің бағдарламаңыздың шығарған нәтижесі: '{actual_output}'</i>",
                            "level": user_data["level"]})

    except subprocess.TimeoutExpired:
        user_data["level"] = max(0, user_data["level"] - 10)
        return jsonify({"status": "error", "message": "[ҚАТЕ]: Шексіз цикл немесе бағдарлама тым ұзақ орындалды.",
                        "level": user_data["level"]})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Жүйелік қате: {e}", "level": user_data["level"]})


if __name__ == '__main__':
    app.run(debug=True)