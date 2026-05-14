int max2(int a, int b) {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}

main() {
    int i;
    int best;
    best = 0;
    for (i = 0; i < 5; i = i + 1) {
        best = max2(best, i);
    }
    write(best);
}
