const int limit = 10;
char tag = 'A';

main() {
    int i;
    int sum;
    i = 0;
    sum = 0;
    while (i < limit && sum != 99) {
        sum = sum + i * 2 / 1 % 5;
        i = i + 1;
    }
    write("lexical ok");
    write(sum);
}
