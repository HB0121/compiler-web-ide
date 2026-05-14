const int limit = 3;

int add(int a, int b) {
    return a + b;
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
