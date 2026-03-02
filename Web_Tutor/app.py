from flask import Flask, render_template, request, jsonify, Response
import subprocess
import json
import cv2
import threading
import time
import winsound
from ultralytics import YOLO
from google import genai

app = Flask(__name__)

# ЖАСАНДЫ ИНТЕЛЛЕКТ БАПТАУЛАРЫ
API_KEY = "AIzaSyDD--7HNIReLv21N5wVca95Zto55xcAL_U"
client = genai.Client(api_key=API_KEY)

# ЭРГОНОМИКА ЖӘНЕ КАМЕРА БАПТАУЛАРЫ
GLOBAL_SCORE = 100
POSTURE_STATUS = "GOOD"
camera_frame = None
model_pose = YOLO('yolov8n-pose.pt')


# Бұл функция артқы фонда (background) үзіліссіз камераны оқиды
def vision_thread():
    global camera_frame, GLOBAL_SCORE, POSTURE_STATUS
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    slouch_timer = 0

    while True:
        success, frame = cap.read()
        if not success:
            time.sleep(0.1)
            continue

        results_pose = model_pose(frame, verbose=False)
        POSTURE_STATUS = "GOOD"

        for r in results_pose:
            if r.keypoints is not None and len(r.keypoints.xy) > 0:
                kp = r.keypoints.xy[0]
                if len(kp) >= 7 and kp[0][1] > 0 and kp[5][1] > 0:
                    nose_y = int(kp[0][1])
                    l_sh_y = int(kp[5][1])
                    r_sh_y = int(kp[6][1])

                    avg_shoulder_y = (l_sh_y + r_sh_y) / 2
                    neck_dist = avg_shoulder_y - nose_y

                    cv2.circle(frame, (int(kp[0][0]), nose_y), 6, (0, 255, 255), -1)
                    cv2.circle(frame, (int(kp[5][0]), l_sh_y), 6, (255, 0, 255), -1)
                    cv2.circle(frame, (int(kp[6][0]), r_sh_y), 6, (255, 0, 255), -1)

                    if neck_dist < 165:  # Осы санды өз мойныңыздың қашықтығына қарай өзгерте аласыз
                        POSTURE_STATUS = "BAD (Enkeime!)"
                        slouch_timer += 1
                        if slouch_timer > 30:  # 30 кадр бойы бүкірейсе
                            GLOBAL_SCORE -= 5
                            winsound.Beep(750, 500)
                            slouch_timer = 0
                    else:
                        slouch_timer = 0

        # Кадрды сайтқа жіберу үшін суретке (jpeg) айналдырамыз
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            camera_frame = buffer.tobytes()


# Камераны бөлек ағында іске қосу
threading.Thread(target=vision_thread, daemon=True).start()


# Сайтқа суретті жіберетін генератор
def generate_frames():
    while True:
        if camera_frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + camera_frame + b'\r\n')
        time.sleep(0.05)


@app.route('/')
def home():
    return render_template('index.html')


# 1-API: Видеоны сайтқа жіберу
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# 2-API: Денсаулық ұпайын сайтқа жіберу
@app.route('/get_score')
def get_score():
    return jsonify({"score": GLOBAL_SCORE, "posture": POSTURE_STATUS})


# 3-API: AI-ДАН ТАПСЫРМА СҰРАУ
@app.route('/get_task', methods=['POST'])
def get_task():
    data = request.json
    topic = data.get('topic', 'Кіріспе')
    level = data.get('level', 10)

    prompt = f"""
    Сен C++ ұстазысың. Маған '{topic}' тақырыбы бойынша 1 оңай есеп ойлап тап.
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
        return jsonify(json.loads(text))
    except Exception as e:
        return jsonify({"desc": f"Қате шықты. Мынаны жазыңыз: std::cout << 'Test';", "hint": "std::cout << 'Test';"})


# 4-API: КОДТЫ КОМПИЛЯЦИЯЛАУ ЖӘНЕ ЛОГИКАЛЫҚ ТЕКСЕРУ
@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '')
    task_desc = data.get('task_desc', '')

    cpp_template = f"""#include <iostream>
#include <windows.h>
using namespace std;
int main() {{
    SetConsoleOutputCP(CP_UTF8);
    {code}
    return 0;
}}"""

    with open("temp_code.cpp", "w", encoding="utf-8") as f:
        f.write(cpp_template)

    try:
        compile_process = subprocess.run(["g++", "temp_code.cpp", "-o", "temp_run.exe"], capture_output=True, text=True,
                                         encoding="utf-8", errors="replace")

        if compile_process.returncode != 0:
            err = compile_process.stderr.split("temp_code.cpp")[
                1] if "temp_code.cpp" in compile_process.stderr else compile_process.stderr
            ai_prompt = f"Тапсырма: {task_desc}. Код: {code}. Қате: {err[:300]}. Қатені қазақша түсіндір (2 сөйлем)."
            ai_response = client.models.generate_content(model='gemini-2.5-flash', contents=ai_prompt).text
            return jsonify({"status": "error", "message": f"[СИНТАКСИС ҚАТЕСІ]: {ai_response}"})

        run_process = subprocess.run(["temp_run.exe"], capture_output=True, text=True, encoding="utf-8",
                                     errors="replace", timeout=3)
        actual_output = run_process.stdout.strip()

        eval_prompt = f"""Сен қатаң ұстазсың. Тапсырма: "{task_desc}". Код: "{code}". Нәтиже: "{actual_output}". Дұрыс па? Иә болса "YES", жоқ болса "NO|" деп қатені қазақша түсіндір."""
        eval_response = client.models.generate_content(model='gemini-2.5-flash', contents=eval_prompt).text.strip()

        if eval_response.startswith("YES"):
            return jsonify({"status": "success", "message": f"[ТАМАША]: Код дұрыс! Нәтиже: {actual_output}"})
        else:
            feedback = eval_response.replace("NO|", "").replace("NO", "").strip()
            return jsonify({"status": "error",
                            "message": f"[ЛОГИКАЛЫҚ ҚАТЕ]: {feedback}<br><i>Шыққан нәтиже: '{actual_output}'</i>"})

    except Exception as e:
        return jsonify({"status": "error", "message": f"Жүйелік қате: {e}"})


if __name__ == '__main__':
    app.run(debug=True, threaded=True)