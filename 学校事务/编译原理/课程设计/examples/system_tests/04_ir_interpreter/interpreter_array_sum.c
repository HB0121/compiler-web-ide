int a[4];

main() {
    int i;
    int sum;
    a[0] = 1;
    a[1] = 2;
    a[2] = 3;
    a[3] = 4;
    i = 0;
    sum = 0;
    while (i < 4) {
        sum = sum + a[i];
        i = i + 1;
    }
    write(sum);
}
