main() {
    int i;
    int j;
    int total;
    total = 0;
    for (i = 0; i < 3; i = i + 1) {
        j = 0;
        while (j < 2) {
            total = total + i + j;
            j = j + 1;
        }
    }
    write(total);
}
