#include <iostream>
using namespace std;
int main() {
int total_seconds = 3665; int h = total_seconds / 3600; int m = (total_seconds % 3600) / 60; int s = total_seconds % 60; std::cout << h << ":" << m << ":" << s;
return 0;
}