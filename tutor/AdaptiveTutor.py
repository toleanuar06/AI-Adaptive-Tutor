import time
import subprocess
import os
from google import genai

# ==========================================
# 0. ЖАСАНДЫ ИНТЕЛЛЕКТ БАПТАУЛАРЫ
# ==========================================
# ОСЫ ЖЕРГЕ GOOGLE AI STUDIO-ДАН АЛҒАН КІЛТТІ ҚОЙЫҢЫЗ:
API_KEY = "AIzaSyDr8L74F7X32fBBuN3mQBxd7jb4YM6x860"

# ==========================================
# 1. ДЕРЕКҚОР ЖӘНЕ ОҚУ ПРОГРАММАСЫ
# ==========================================
TASKS = {
    "Basics": [
        {"level": 1, "desc": "C++ тілінде экранға 'Hello' сөзін шығаратын код жазыңыз.",
         "hint": "Көмек: std::cout пайдаланыңыз."},
        {"level": 2, "desc": "C++ тілінде a және b айнымалыларын қосып, нәтижесін шығарыңыз."}
    ],
    "Loops": [
        {"level": 1, "desc": "'for' циклі арқылы 0-ден 5-ке дейін сандарды шығарыңыз.",
         "hint": "Көмек: for(int i=0; i<5; i++)"},
        {"level": 2, "desc": "'while' циклі арқылы шексіз цикл емес, 3 рет айналатын код жазыңыз."}
    ]
}


# ==========================================
# 2. ОҚУШЫ ПРОФИЛІ (KNOWLEDGE TRACING)
# ==========================================
class KnowledgeProfile:
    def __init__(self, name):
        self.name = name
        self.skills = {"Basics": 50, "Loops": 50}

    def update_skill(self, topic, is_correct):
        if is_correct:
            self.skills[topic] = min(100, self.skills[topic] + 20)
        else:
            self.skills[topic] = max(0, self.skills[topic] - 15)

    def get_skill_level(self, topic):
        return self.skills[topic]


# ==========================================
# 3. НАҒЫЗ КОМПИЛЯТОР + AI ҰСТАЗ (LLM)
# ==========================================
class CodeAnalyzer:
    def __init__(self):
        # Жаңа SDK арқылы клиентті іске қосу
        self.client = genai.Client(api_key=API_KEY)

    def get_ai_feedback(self, code, task_desc, error_text):
        prompt = f"""
        Сен C++ бағдарламалау тілінен дәріс беретін тәжірибелі, өте мейірімді ұстазсың.
        Оқушының тапсырмасы: "{task_desc}"
        Оқушы жазған код: "{code}"
        Компилятор мынадай қате шығарды: "{error_text}"

        Сенің міндетің: Осы қатенің неліктен шыққанын қазақ тілінде қарапайым әрі түсінікті етіп түсіндіру.
        Ескерту: Дұрыс кодты ешқашан толығымен жазып берме! Тек қатені нұсқап, оқушының өзі ойлануы үшін кішкене ғана бағыт (hint) бер. Жауабың қысқа болсын (2-3 сөйлем).
        """
        try:
            # Жаңа заманауи модельді қолданамыз
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"AI жүйесіне қосылуда қате шықты: {e}"

    def analyze(self, code, topic, task_desc):
        cpp_template = f"""
        #include <iostream>
        using namespace std;
        int main() {{
            {code}
            return 0;
        }}
        """

        with open("temp_code.cpp", "w", encoding="utf-8") as f:
            f.write(cpp_template)

        try:
            compile_process = subprocess.run(
                ["g++", "temp_code.cpp", "-o", "temp_run.exe"],
                capture_output=True, text=True
            )
        except Exception as e:
            return False, f"[ЖҮЙЕЛІК ҚАТЕ]: g++ табылмады. {e}"

        # ЕГЕР СИНТАКСИС ҚАТЕ БОЛСА -> AI-ДАН КӨМЕК СҰРАЙМЫЗ
        if compile_process.returncode != 0:
            error_msg = compile_process.stderr.split("temp_code.cpp")[
                1] if "temp_code.cpp" in compile_process.stderr else compile_process.stderr

            print("\n[AI ҰСТАЗ ОЙЛАНЫП ЖАТЫР...]")
            ai_explanation = self.get_ai_feedback(code, task_desc, error_msg.strip()[:300])

            return False, f"[AI ҰСТАЗДЫҢ КЕҢЕСІ]:\n{ai_explanation}"

        # ЛОГИКАЛЫҚ ТЕКСЕРІС
        if topic == "Basics":
            if "cout" not in code:
                return False, "[ЛОГИКАЛЫҚ ҚАТЕ]: Экранға ештеңе шығарған жоқсыз ('cout' ұмыттыңыз)."
            return True, "[ТАМАША]: Код сәтті компиляциядан өтті және логикасы дұрыс!"

        elif topic == "Loops":
            if "while" not in code and "for" not in code:
                return False, "[ЛОГИКАЛЫҚ ҚАТЕ]: Тапсырма шарты орындалмады. Цикл қолданыңыз."
            if "++" not in code and "+=" not in code and "--" not in code:
                return False, "[ЛОГИКАЛЫҚ ҚАТЕ]: Итератор көрсетілмеген. Бұл шексіз циклге әкеледі!"
            return True, "[ТАМАША]: Код сәтті компиляциядан өтті!"

        return False, "[ҚАТЕ]: Жүйе кодты бағалай алмады."


# ==========================================
# 4. АДАПТИВТІ ОҚЫТУ ЖҮЙЕСІ (AI LOGIC)
# ==========================================
class IntelligentTutor:
    def __init__(self, student_name):
        self.profile = KnowledgeProfile(student_name)
        self.analyzer = CodeAnalyzer()

    def start_lesson(self, topic):
        print(f"\n{'=' * 40}\n[ПӘН]: {topic} тақырыбы басталды\n{'=' * 40}")

        while True:
            current_level = self.profile.get_skill_level(topic)
            print(f"\n[СІЗДІҢ ДЕҢГЕЙІҢІЗ]: {current_level}%")

            difficulty = 0 if current_level < 60 else 1
            task = TASKS[topic][difficulty]

            print(f"\n>>> ТАПСЫРМА (Қиындық деңгейі - {task['level']}):")
            print(task['desc'])

            if current_level < 40 and "hint" in task:
                print(f"[ЖҮЙЕЛІК КӨМЕКШІ]: {task['hint']}")

            print("-" * 40)
            print("C++ кодыңыздан бір жол жазыңыз (немесе шығу үшін 'q' басыңыз):")
            user_code = input(">> ")

            if user_code.lower() == 'q':
                break

            # ТАЛДАУҒА ЖІБЕРУ
            is_correct, feedback = self.analyzer.analyze(user_code, topic, task['desc'])
            print(f"\n{feedback}")

            self.profile.update_skill(topic, is_correct)

            if self.profile.get_skill_level(topic) >= 100:
                print(f"\n[ҚҰТТЫҚТАЙМЫЗ!]: Сіз '{topic}' тақырыбын толық меңгердіңіз!")
                break

            time.sleep(1)


# ==========================================
# БАҒДАРЛАМАНЫ ІСКЕ ҚОСУ
# ==========================================
if __name__ == "__main__":
    print("AI-Adaptive Оқу платформасына қош келдіңіз!")
    name = input("Есіміңіз кім? ")
    tutor = IntelligentTutor(name)

    tutor.start_lesson("Basics")
    tutor.start_lesson("Loops")

    print("\nОқу курсы аяқталды. Сау болыңыз!")