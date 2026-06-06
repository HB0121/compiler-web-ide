const int limit = 4;

int add(int a, int b) {
    int c;
    c = a + b;
    return c;
}

main() {
    int i;
    int total;
    i = 0;
    total = 0;
    while (i < limit) {
        total = add(total, i);
        i = i + 1;
    }
    write(total);
}
