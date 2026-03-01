import time
import time
import subprocess
import os

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
        # Оқушының әр тақырып бойынша білім деңгейі (Бастапқыда 50%)
        self.skills = {"Basics": 50, "Loops": 50}

    def update_skill(self, topic, is_correct):
        if is_correct:
            self.skills[topic] = min(100, self.skills[topic] + 20)  # Дұрыс болса 20% қосамыз
        else:
            self.skills[topic] = max(0, self.skills[topic] - 15)  # Қате болса 15% аламыз

    def get_skill_level(self, topic):
        return self.skills[topic]


# ==========================================
# 3. НАҒЫЗ КОМПИЛЯТОРМЕН ТАЛДАУ (g++ INTEGRATION)
# ==========================================
class CodeAnalyzer:
    def analyze(self, code, topic):
        # 1. Оқушының кодын толыққанды C++ бағдарламасына айналдырамыз
        cpp_template = f"""
        #include <iostream>
        using namespace std;
        int main() {{
            {code}
            return 0;
        }}
        """

        # 2. Оны уақытша файлға сақтаймыз
        with open("../.gitignore/temp_code.cpp", "w", encoding="utf-8") as f:
            f.write(cpp_template)

        # 3. Компьютердегі g++ компиляторын іске қосамыз
        try:
            compile_process = subprocess.run(
                ["g++", "temp_code.cpp", "-o", "temp_run.exe"],
                capture_output=True, text=True
            )
        except Exception as e:
            return False, f"[ЖҮЙЕЛІК ҚАТЕ]: g++ компиляторы табылмады немесе іске қосылмады. {e}"

        # 4. ЕГЕР СИНТАКСИС ҚАТЕ БОЛСА (g++ қате тапса)
        if compile_process.returncode != 0:
            # Қатенің мәтінін оқушыға түсінікті етіп қысқартып береміз
            error_msg = compile_process.stderr.split("temp_code.cpp")[
                1] if "temp_code.cpp" in compile_process.stderr else compile_process.stderr
            return False, f"[КОМПИЛЯЦИЯ ҚАТЕСІ]: Сіздің кодыңызда синтаксистік қате бар:\n{error_msg.strip()[:250]}"

        # 5. ЕГЕР КОМПИЛЯЦИЯДАН СӘТТІ ӨТСЕ, ЛОГИКАСЫН ТЕКСЕРЕМІЗ
        if topic == "Basics":
            if "cout" not in code:
                return False, "[ЛОГИКАЛЫҚ ҚАТЕ]: Код жұмыс істеп тұр, бірақ экранға ештеңе шығарған жоқсыз ('cout' ұмыттыңыз)."
            return True, "[ТАМАША]: Код сәтті компиляциядан өтті және логикасы дұрыс!"

        elif topic == "Loops":
            if "while" not in code and "for" not in code:
                return False, "[ЛОГИКАЛЫҚ ҚАТЕ]: Код жұмыс істейді, бірақ тапсырма шарты орындалмады. Цикл (for/while) қолданыңыз."
            if "++" not in code and "+=" not in code and "--" not in code:
                return False, "[ЛОГИКАЛЫҚ ҚАТЕ]: Итератор (қадам) көрсетілмеген. Бұл шексіз циклге әкелуі мүмкін!"
            return True, "[ТАМАША]: Код сәтті компиляциядан өтті және цикл дұрыс жазылған!"

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
            # Оқушының қазіргі деңгейін анықтау
            current_level = self.profile.get_skill_level(topic)
            print(f"\n[СІЗДІҢ ДЕҢГЕЙІҢІЗ]: {current_level}%")

            # ҚИЫНДЫҚТЫ БЕЙІМДЕУ (SCAFFOLDING)
            # Егер білім деңгейі 60%-дан төмен түсіп кетсе, жеңіл есеп береміз (level 1)
            difficulty = 0 if current_level < 60 else 1
            task = TASKS[topic][difficulty]

            print(f"\n>>> ТАПСЫРМА (Қиындық деңгейі - {task['level']}):")
            print(task['desc'])

            # Егер оқушы қатты қинала бастаса (деңгейі < 40%), көмек көрсетеміз
            if current_level < 40 and "hint" in task:
                print(f"[AI КӨМЕКШІ]: {task['hint']}")

            print("-" * 40)
            print("C++ кодыңыздан бір жол жазыңыз (немесе шығу үшін 'q' басыңыз):")
            user_code = input(">> ")

            if user_code.lower() == 'q':
                break

            # 3. Кодты талдау және бағалау
            is_correct, feedback = self.analyzer.analyze(user_code, topic)
            print(f"\n{feedback}")

            # 4. Профильді жаңарту
            self.profile.update_skill(topic, is_correct)

            # Егер деңгей 100% болса, тақырыпты жабамыз
            if self.profile.get_skill_level(topic) >= 100:
                print(f"\n[ҚҰТТЫҚТАЙМЫЗ!]: Сіз '{topic}' тақырыбын толық меңгердіңіз!")
                break

            time.sleep(1)


# ==========================================
# БАҒДАРЛАМАНЫ ІСКЕ ҚОСУ
# ==========================================
if __name__ == "__main__":
    print("Интерактивті Адаптивті Оқу платформасына қош келдіңіз!")
    name = input("Есіміңіз кім? ")

    tutor = IntelligentTutor(name)

    # Алдымен "Basics" тақырыбын оқытамыз
    tutor.start_lesson("Basics")

    # Одан кейін "Loops" тақырыбына өтеміз
    tutor.start_lesson("Loops")

    print("\nОқу курсы аяқталды. Сау болыңыз!")