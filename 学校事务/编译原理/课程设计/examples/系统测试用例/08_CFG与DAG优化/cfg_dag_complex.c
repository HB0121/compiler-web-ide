main() {
    int a;
    int b;
    int c;
    int d;
    int x;
    int y;
    int z;
    a = 10;
    b = 5;
    c = a + b;
    d = a + b;
    x = c * d;
    if (x > 20) {
        y = a + b;
        z = y * d;
    } else {
        y = a - b;
        z = y + d;
    }
    write(z);
}
