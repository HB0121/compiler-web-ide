main() {
    int i;
    int odd;
    i = 0;
    odd = 0;
    while (i < 5) {
        if (i % 2 != 0) {
            odd = odd + 1;
        }
        i = i + 1;
    }
    write(odd);
}
