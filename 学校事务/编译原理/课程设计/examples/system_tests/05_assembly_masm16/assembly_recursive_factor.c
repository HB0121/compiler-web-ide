int factor(int n) {
    int result;
    if (n <= 1) {
        result = 1;
    } else {
        result = n * factor(n - 1);
    }
    return result;
}

main() {
    int value;
    value = 5;
    write(factor(value));
}
