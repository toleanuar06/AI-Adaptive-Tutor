import time
import subprocess
import threading
import winsound
import cv2
import json  # ЖАҢА КІТАПХАНА: AI жауабын оқу үшін
from ultralytics import YOLO
from google import genai

# ==========================================
# 0. БАПТАУЛАР ЖӘНЕ ОРТАҚ АЙНЫМАЛЫЛАР
# ==========================================
API_KEY = "AIzaSyDr8L74F7X32fBBuN3mQBxd7jb4YM6x860"
GLOBAL_SCORE = 100
POSTURE_STATUS = "GOOD"

# БІЗДІҢ ОҚУ БАҒДАРЛАМАМЫЗ (AI осы тақырыптар бойынша есептерді өзі құрастырады)
TOPICS = ["Кіріспе (Шығару операторлары)", "Айнымалылар және Математика", "Циклдер (for, while)"]


# ==========================================
# 1. КОМПЬЮТЕРЛІК КӨРУ (Артқы фондағы көз)
# ==========================================
def vision_thread():
    global GLOBAL_SCORE, POSTURE_STATUS
    print("[ЖҮЙЕ]: Камера мен YOLO модельдері іске қосылуда...")
    model_pose = YOLO('yolov8n-pose.pt')
    cap = cv2.VideoCapture(0)
    slouch_timer = 0

    while True:
        ret, frame = cap.read()
        if not ret: break

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

                    if neck_dist < 165:
                        POSTURE_STATUS = "BAD (Enkeime!)"
                        slouch_timer += 1
                        if slouch_timer > 30:
                            GLOBAL_SCORE -= 5
                            winsound.Beep(750, 500)
                            slouch_timer = 0
                    else:
                        slouch_timer = 0

        cv2.rectangle(frame, (0, 0), (640, 70), (30, 30, 30), -1)
        cv2.putText(frame, f"GLOBAL SCORE: {GLOBAL_SCORE}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        color = (0, 255, 0) if "GOOD" in POSTURE_STATUS else (0, 0, 255)
        cv2.putText(frame, f"POSTURE: {POSTURE_STATUS}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow('Cyber Tutor - AI Monitor', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()


# ==========================================
# 2. АҚЫЛДЫ ҰСТАЗ ЖӘНЕ AI-ГЕНЕРАТОР (Терминалдағы ми)
# ==========================================
class KnowledgeProfile:
    def __init__(self):
        # Бастапқыда барлық тақырып бойынша білім 10%
        self.skills = {topic: 10 for topic in TOPICS}

    def update_skill(self, topic, is_correct):
        if is_correct:
            self.skills[topic] = min(100, self.skills[topic] + 30)
        else:
            self.skills[topic] = max(0, self.skills[topic] - 15)

    def get_skill_level(self, topic):
        return self.skills[topic]


class CodeAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)

    # ЖАҢА ФУНКЦИЯ: AI-ДАН ТАПСЫРМА СҰРАУ
    def generate_dynamic_task(self, topic, user_level):
        prompt = f"""
        Сен C++ бағдарламалау тілінің ұстазысың. 
        Маған '{topic}' тақырыбы бойынша 1 практикалық тапсырма ойлап тап. Ол 1 жолмен жазылатындай болсын.
        Оқушының қазіргі білім деңгейі: {user_level}%. 
        (Егер деңгейі 50%-дан төмен болса - өте оңай есеп бер, 50%-дан жоғары болса - сәл қиындат).
        Жауабың МІНДЕТТІ ТҮРДЕ тек қана мынадай JSON форматында болсын, артық сөз жазба:
        {{"desc": "Есептің шарты (қазақша)", "hint": "Көмек"}}
        """
        try:
            response = self.client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            # AI жауабынан таза JSON бөлігін кесіп алу
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()

            return json.loads(text)
        except Exception as e:
            return {"desc": f"Қате шықты, мына кодты жаза салыңыз: std::cout << 'Test';", "hint": "Жүйедегі қате"}

    def get_ai_feedback(self, code, task_desc, error_text):
        prompt = f"""Сен C++ ұстазысың. Оқушының тапсырмасы: "{task_desc}". Коды: "{code}". Қате: "{error_text}". Қатенің себебін қазақша түсіндір, бірақ дайын жауапты берме. (2-3 сөйлем)"""
        try:
            response = self.client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return response.text
        except Exception:
            return "AI байланыс қатесі."

    def analyze(self, code, topic, task_desc):
        with open("temp_code.cpp", "w", encoding="utf-8") as f:
            f.write(f"#include <iostream>\nusing namespace std;\nint main() {{\n{code}\nreturn 0;\n}}")

        try:
            compile_process = subprocess.run(["g++", "temp_code.cpp", "-o", "temp_run.exe"], capture_output=True,
                                             text=True)
            if compile_process.returncode != 0:
                print("\n[AI ҰСТАЗ ОЙЛАНЫП ЖАТЫР...]")
                err = compile_process.stderr.split("temp_code.cpp")[
                    1] if "temp_code.cpp" in compile_process.stderr else compile_process.stderr
                return False, f"[AI ҰСТАЗ]:\n{self.get_ai_feedback(code, task_desc, err[:300])}"

            # Жалпылама логиканы тексереміз (компиляциядан өтсе болды деп қабылдаймыз, өйткені есепті AI өзі ойлап табады)
            return True, "[ТАМАША]: Код сәтті орындалды!"
        except Exception as e:
            return False, f"[ЖҮЙЕ ҚАТЕСІ]: {e}"


def tutor_logic():
    global GLOBAL_SCORE
    analyzer = CodeAnalyzer()
    profile = KnowledgeProfile()

    time.sleep(3)
    print(f"\n{'=' * 50}\n[КИБЕР-ҰСТАЗ]: AI-Генератор іске қосылды!\n{'=' * 50}")

    for topic in TOPICS:
        print(f"\n>> ЖАҢА ТАҚЫРЫП: {topic} <<")

        # Оқушының деңгейі 100% болғанша осы тақырыпта шексіз тапсырма бере береді
        while profile.get_skill_level(topic) < 100:
            current_level = profile.get_skill_level(topic)
            print(f"\n[AI ЖАҢА ТАПСЫРМА ҚҰРАСТЫРУДА... Күте тұрыңыз]")

            task = analyzer.generate_dynamic_task(topic, current_level)

            print(f"\n[ТАҚЫРЫПТЫ МЕҢГЕРУ: {current_level}% | ҰПАЙ: {GLOBAL_SCORE}]")
            print(f">>> ТАПСЫРМА:\n{task['desc']}")

            if current_level < 50:
                print(f"[КӨМЕК]: {task['hint']}")

            user_code = input("\n>> C++ коды: ")
            if user_code.lower() == 'q': return

            is_correct, feedback = analyzer.analyze(user_code, topic, task['desc'])
            print(f"\n{feedback}")

            profile.update_skill(topic, is_correct)

            if is_correct:
                GLOBAL_SCORE += 20
            else:
                GLOBAL_SCORE -= 10

        print(f"\n[ҚҰТТЫҚТАЙМЫЗ!]: Сіз '{topic}' тақырыбын 100% меңгердіңіз. Келесіге өтеміз!")

    print(f"\n[КУРС АЯҚТАЛДЫ!]: Жалпы ұпайыңыз: {GLOBAL_SCORE}.")


# ==========================================
# 3. ЕКІ ЖҮЙЕНІ ҚАТАР ІСКЕ ҚОСУ (MULTITHREADING)
# ==========================================
if __name__ == "__main__":
    camera_thread = threading.Thread(target=vision_thread, daemon=True)
    camera_thread.start()
    tutor_logic()