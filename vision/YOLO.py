import cv2
import os
from ultralytics import YOLO

# ЕКІ МОДЕЛЬДІ ҚАТАР ЖҮКТЕЙМІЗ
model_obj = YOLO('yolov8n.pt')  # Заттар үшін
model_pose = YOLO('yolov8n-pose.pt')  # Қаңқа үшін (алғаш қосқанда жүктеледі)

cap = cv2.VideoCapture(0)
print("Камера іске қосылды. Тоқтату үшін 'q' пернесін басыңыз.")


def read_ui_data():
    if not os.path.exists("../.gitignore/ui_data.txt"):
        return "Unknown", "0", "KUTU", "Derektter kutilude..."
    try:
        with open("../.gitignore/ui_data.txt", "r") as f:
            lines = f.read().splitlines()
            if len(lines) >= 4:
                return lines[0], lines[1], lines[2], lines[3]
    except Exception:
        pass
    return "Unknown", "0", "...", "..."


while True:
    ret, frame = cap.read()
    if not ret: break

    # Екі модельден де нәтиже алу
    results_obj = model_obj(frame, verbose=False)
    results_pose = model_pose(frame, verbose=False)

    bottle_coords = None
    device_coords = None
    slouch_status = 0  # 0 - Тік отыр, 1 - Бүкірейіп отыр

    # 1. ЗАТТАРДЫ ІЗДЕУ
    for r in results_obj:
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf < 0.60: continue
            cls_id = int(box.cls[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            if cls_id in [39, 41]:
                bottle_coords = (cx, cy)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            elif cls_id in [0, 73, 76]:
                device_coords = (cx, cy)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

    # 2. ДЕНЕНІҢ ҚАЛПЫН ТАЛДАУ (Pose Estimation)
    for r in results_pose:
        if r.keypoints is not None and len(r.keypoints.xy) > 0:
            kp = r.keypoints.xy[0]  # Бірінші табылған адамның нүктелері

            # Егер модель нүктелерді сенімді тапса (координаттары 0-ден үлкен болса)
            if len(kp) >= 7 and kp[0][1] > 0 and kp[5][1] > 0 and kp[6][1] > 0:
                nose_y = int(kp[0][1])
                l_sh_y = int(kp[5][1])
                r_sh_y = int(kp[6][1])

                # Экранға нүктелерді сызу (Мұрын және екі иық)
                cv2.circle(frame, (int(kp[0][0]), nose_y), 6, (0, 255, 255), -1)
                cv2.circle(frame, (int(kp[5][0]), l_sh_y), 6, (255, 0, 255), -1)
                cv2.circle(frame, (int(kp[6][0]), r_sh_y), 6, (255, 0, 255), -1)

                # Математика: Иықтардың орташа биіктігінен мұрынды алу
                # Математика: Иықтардың орташа биіктігінен мұрынды алу
                avg_shoulder_y = (l_sh_y + r_sh_y) / 2
                neck_dist = avg_shoulder_y - nose_y

                # НАҚТЫ САНДЫ ЭКРАНҒА ШЫҒАРУ (Калибровка үшін)
                cv2.putText(frame, f"Moyn uzyndygy: {int(neck_dist)} px", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (255, 255, 0), 2)

                # Шекті (threshold) 40-тан 75-ке көтердік (бұл сіздің камераңызға көбірек сай келуі керек)
                # Шекті сіздің камераңызға бейімдедік: 165
                if neck_dist < 160:
                    slouch_status = 1
                    cv2.putText(frame, "POSTURE: BAD (Enkeime!)", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255),
                                2)
                else:
                    cv2.putText(frame, "POSTURE: GOOD", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # 3. ДЕРЕКТЕРДІ C++ ҮШІН ФАЙЛҒА ЖАЗУ (Енді 5 сан!)
    bx, by = bottle_coords if bottle_coords else (-1, -1)
    dx, dy = device_coords if device_coords else (-1, -1)

    try:
        with open("../.gitignore/coords.txt", "w") as f:
            f.write(f"{bx} {by} {dx} {dy} {slouch_status}")
    except:
        pass

    # ================= GUI БӨЛІГІ =================
    user, score, status, message = read_ui_data()
    cv2.rectangle(frame, (0, 0), (640, 80), (30, 30, 30), -1)
    cv2.putText(frame, f"User: {user} | Score: {score}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    color = (0, 255, 0) if "KALYPTY" in status else (0, 0, 255)
    cv2.putText(frame, f"Status: {status}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, message, (300, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    # ==============================================

    cv2.imshow('Интерактивті Ассистент (Vision & Pose)', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()