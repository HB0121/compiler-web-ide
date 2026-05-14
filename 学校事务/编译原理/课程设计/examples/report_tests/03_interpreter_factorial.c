main() {
    int n;
    int i;
    int result;
    n = 5;
    i = 1;
    result = 1;
    while (i <= n) {
        result = result * i;
        i = i + 1;
    }
    write(result);
}
