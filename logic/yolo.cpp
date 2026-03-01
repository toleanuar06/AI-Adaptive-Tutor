#include <iostream>
#include <fstream>
#include <cmath>
#include <windows.h> // Beep дыбысы үшін керек
#include <thread>
#include <chrono>
#include <string>

using namespace std;

struct Point { int x, y; };

class Assistant {
private:
    double safeDistance = 250.0;
    int liquidWarningCount = 0;
    int postureWarningCount = 0; // Дене қалпының қателерін санайтын айнымалы
    string userName;
    int totalErrors = 0;
    int score = 100;

    void loadProfile() {
        ifstream file("profile_" + userName + ".txt");
        if (file.is_open()) {
            file >> totalErrors >> score;
            file.close();
        } else {
            totalErrors = 0;
            score = 100;
        }
    }

    void saveProfile() {
        ofstream file("profile_" + userName + ".txt");
        if (file.is_open()) {
            file << totalErrors << " " << score;
            file.close();
        }
    }

    void updateUI(string status, string message) {
        ofstream file("ui_data.txt");
        if (file.is_open()) {
            file << userName << "\n" << score << "\n" << status << "\n" << message;
            file.close();
        }
    }

public:
    Assistant(string name) {
        userName = name;
        loadProfile();
        cout << "\n[ЖҮЙЕ]: Қош келдіңіз, " << userName << "!" << endl;
        cout << "[ЖҮЙЕ]: Ұпайыңыз: " << score << " | Тарихтағы қателер: " << totalErrors << endl;
        updateUI("KOSYLDY", "Zhuie iske kosyldy. Daiynbyz.");
        this_thread::sleep_for(chrono::seconds(2));
        system("cls");
        cout << "=========================================" << endl;
        cout << "[ЖҮЙЕ]: Бақылау жүйесі жұмыс істеп тұр..." << endl;
        cout << "=========================================" << endl;
    }

    double getDistance(Point p1, Point p2) {
        return sqrt(pow(p2.x - p1.x, 2) + pow(p2.y - p1.y, 2));
    }

    // Бұл жерде енді 5-ші параметр (slouch) қабылдаймыз
    void analyzeSituation(Point liquid, Point device, int slouch) {

        // 1. Сұйықтық қаупін тексеру (егер кадрда бөтелке бар болса)
        bool isLiquidDanger = false;
        if (liquid.x != -1 && liquid.y != -1 && device.x != -1 && device.y != -1) {
            if (getDistance(liquid, device) < safeDistance) {
                isLiquidDanger = true;
            }
        }

        if (isLiquidDanger) {
            liquidWarningCount++;
            updateUI("KAUIP!", "Suiyktyk tym zhakyn!");

            if (liquidWarningCount >= 5) {
                updateUI("TAPSIRMA", "Terminalga zhauap beriniz...");
                system("cls");
                cout << "\n>>> ИНТЕРАКТИВТІ ТАПСЫРМА! <<<" << endl;
                cout << "Сұрақ: Су төгілсе, ең бірінші не істеу керек?" << endl;
                cout << "1: Сүрту | 2: Тоқтан ажырату\nЖауабыңыз: ";

                int answer;
                cin >> answer;
                if (answer == 2) {
                    cout << "[ДҰРЫС!]: +10 ұпай!" << endl;
                    score += 10;
                } else {
                    cout << "[ҚАТЕ!]: -15 ұпай!" << endl;
                    score -= 15;
                }
                totalErrors++;
                saveProfile();
                updateUI("KUTU...", "Botelkeni alshak koyiniz...");

                cout << "\nБөтелкені алшақ қойыңыз..." << endl;
                liquidWarningCount = 0;
                this_thread::sleep_for(chrono::seconds(3));

                system("cls");
                cout << "=========================================" << endl;
                cout << "[ЖҮЙЕ]: Бақылау жүйесі жұмыс істеп тұр..." << endl;
                cout << "=========================================" << endl;
            }
        }
        // 2. Дененің қалпын (Эргономика) тексеру
        else if (slouch == 1) {
            postureWarningCount++;
            updateUI("ESKERTU!", "Arkanizdy tik ustanyz! (Slouching)");

            // Егер адам 3 секунд бойы бүкірейіп отырса (10 кадр)
            if (postureWarningCount >= 10) {
                Beep(750, 500); // 750 Гц жиіліктегі дыбыс 0.5 секунд шығады!
                score -= 5;
                saveProfile();
                updateUI("AIYP PUL", "-5 upai. Tik otyrynyz!");

                system("cls");
                cout << "\n[ЭРГОНОМИКА]: Сіз мониторға тым қатты еңкейіп кеттіңіз!" << endl;
                cout << "[ЖАЗА]: -5 ұпай шегерілді. Жалпы ұпай: " << score << endl;
                cout << "Арқаңызды тік ұстаңыз..." << endl;

                this_thread::sleep_for(chrono::seconds(2));

                system("cls");
                cout << "=========================================" << endl;
                cout << "[ЖҮЙЕ]: Бақылау жүйесі жұмыс істеп тұр..." << endl;
                cout << "=========================================" << endl;

                postureWarningCount = 0;
            }
        }
        // 3. Бәрі жақсы болса
        else {
            updateUI("KALYPTY", "Barlygy durys. Zhalgastyrynyz");
            liquidWarningCount = 0;
            postureWarningCount = 0;
        }
    }
};

int main() {
    SetConsoleOutputCP(CP_UTF8);
    string name;
    cout << "Есіміңізді енгізіңіз (ағылшынша): ";
    cin >> name;

    Assistant bot(name);

    while (true) {
        ifstream file("coords.txt");
        if (file.is_open()) {
            int bx, by, dx, dy, slouch;
            // Енді 5 санды оқимыз
            if (file >> bx >> by >> dx >> dy >> slouch) {
                Point bottle = {bx, by};
                Point device = {dx, dy};
                bot.analyzeSituation(bottle, device, slouch);
            }
            file.close();
        }
        this_thread::sleep_for(chrono::milliseconds(300));
    }
    return 0;
}