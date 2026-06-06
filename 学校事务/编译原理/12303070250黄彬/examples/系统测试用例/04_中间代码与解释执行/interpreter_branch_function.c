int abs_value(int x) {
    if (x < 0) {
        return 0 - x;
    }
    return x;
}

main() {
    int a;
    int b;
    a = 0 - 7;
    b = abs_value(a);
    write(b);
}
