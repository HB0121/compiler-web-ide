int square(int x) {
    return x * x;
}

main() {
    int a;
    int b;
    a = 4;
    b = square(a);
    if (b > 10) {
        write(b);
    } else {
        write(0);
    }
}
