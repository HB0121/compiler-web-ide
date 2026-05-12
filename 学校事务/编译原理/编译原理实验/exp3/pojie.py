with open('input.txt', 'r', encoding='utf-8') as f_in:
    content = f_in.read()

with open('output.txt', 'w', encoding='utf-8') as f_out:
    f_out.write(content)