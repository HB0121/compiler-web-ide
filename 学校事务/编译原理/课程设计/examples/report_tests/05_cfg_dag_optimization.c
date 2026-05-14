main() {
    int a;
    int b;
    int c;
    int d;
    int x;
    int y;
    a = 2;
    b = 3;
    c = a + b;
    d = a + b;
    x = c * d;
    if (x > 20) {
        y = x - 1;
    } else {
        y = x + 1;
    }
    write(y);
}
