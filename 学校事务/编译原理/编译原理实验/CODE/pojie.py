# 调试版本（本地测试用，提交时不要用）
import os

print(f"当前目录：{os.getcwd()}")
print(f"input.txt 存在：{os.path.exists('input.txt')}")

with open('input.txt', 'r', encoding='utf-8') as f:
    content = f.read()

with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print("写入完成")