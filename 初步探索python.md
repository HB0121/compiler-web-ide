# Python 语法详解

## 目录

- Python 简介
- 基本数据类型
    - 数字类型
    - 字符串类型
    - 列表类型
    - 元组类型
    - 字典类型
    - 集合类型
    - 布尔类型
    - 空值类型
- 运算符
    - 算术运算符
    - 比较运算符
    - 逻辑运算符
    - 位运算符
    - 赋值运算符
    - 成员运算符
    - 身份运算符
- 控制流
    - 条件语句
    - 循环语句
        - for 循环
        - while 循环
        - 循环控制语句
- 函数
    - 函数定义
    - 函数参数
    - 返回值
    - 匿名函数
    - 高阶函数
    - 闭包
    - 装饰器
- 模块与包
    - 导入模块
    - 自定义模块
    - 包的使用
- 类与对象
    - 类定义
    - 类的构造方法
    - 类的方法
    - 继承与多态
    - 类的特殊方法
- 异常处理
    - try-except 语句
    - 自定义异常
    - finally 语句
- 文件操作
    - 打开文件
    - 读取文件
    - 写入文件
    - 文件操作上下文管理器
- 常用标准库
    - os 库
    - sys 库
    - math 库
    - datetime 库
    - json 库
    - random 库
    - re 库
    - itertools 库

---

## Python 简介

Python 是一种跨平台的解释型语言，广泛用于 Web 开发、数据分析、人工智能等领域。它支持面向对象、函数式编程以及过程式编程。Python 强调代码的可读性和简洁性，使用缩进来表示代码块，简化了许多编程的复杂性。

---

## 基本数据类型

### 数字类型

Python 中的数字有两种基本类型：整数 (`int`) 和浮点数 (`float`)。支持自动类型转换，支持大整数。

x = 10            # 整数类型  
y = 3.1415        # 浮点数类型  
z = 100000000000  # 大整数

**常用数字操作：**

a = 5  
b = 2  
  
print(a + b)  # 加法 7  
print(a - b)  # 减法 3  
print(a * b)  # 乘法 10  
print(a / b)  # 除法 2.5  
print(a // b) # 整数除法 2  
print(a % b)  # 余数 1  
print(a ** b) # 幂运算 25

### 字符串类型

字符串可以使用单引号或双引号定义。可以进行拼接、切片和多种内置方法操作。

s1 = 'Hello'  
s2 = "World"  
s3 = """This is a   
multi-line string"""  
  
print(s1 + " " + s2)  # 拼接  
print(s1[0:2])         # 切片（输出 'He'）  
print(s1.lower())      # 转小写  
print(s1.upper())      # 转大写

### 列表类型

列表是 Python 中最常用的可变类型，它可以包含不同类型的元素。

lst = [1, 2, 3, "Python", 4.5]  
lst.append(6)            # 添加元素  
lst.remove(2)            # 删除元素  
print(lst[1:4])          # 切片操作

### 元组类型

元组是不可变的有序集合，定义后不能更改其中的内容。

tup = (1, 2, 3, "hello")  
print(tup[1])        # 输出 2

### 字典类型

字典是一种无序的键值对集合，可以通过键快速访问对应的值。

my_dict = {"name": "Alice", "age": 25}  
print(my_dict["name"])  # 访问值  
my_dict["age"] = 26     # 修改值

### 集合类型

集合是一个无序的不重复元素集合。常用于去重和集合操作。

my_set = {1, 2, 3, 4, 5}  
my_set.add(6)         # 添加元素  
my_set.remove(3)      # 删除元素

### 布尔类型

布尔类型有两个值：`True` 和 `False`，常用于条件判断。

x = True  
y = False

### 空值类型

`None` 是 Python 中的空值类型，用于表示缺失的值。

x = None

---

## 运算符

### 算术运算符

x = 10  
y = 3  
  
print(x + y)  # 加法  
print(x - y)  # 减法  
print(x * y)  # 乘法  
print(x / y)  # 除法  
print(x // y) # 整数除法  
print(x % y)  # 余数  
print(x ** y) # 幂运算

### 比较运算符

a = 5  
b = 3  
print(a == b)  # 相等  
print(a != b)  # 不等  
print(a > b)   # 大于  
print(a < b)   # 小于  
print(a >= b)  # 大于等于  
print(a <= b)  # 小于等于

### 逻辑运算符

a = True  
b = False  
print(a and b) # 与运算  
print(a or b)  # 或运算  
print(not a)   # 非运算

### 位运算符

a = 5  # 0101  
b = 3  # 0011  
print(a & b)  # 位与  
print(a | b)  # 位或  
print(a ^ b)  # 位异或  
print(~a)     # 位非  
print(a << 1) # 左移  
print(a >> 1) # 右移

### 赋值运算符

x = 5  
x += 2  # x = x + 2  
x -= 3  # x = x - 3  
x *= 4  # x = x * 4

### 成员运算符

lst = [1, 2, 3, 4]  
print(3 in lst)  # True  
print(5 not in lst)  # True

### 身份运算符

x = [1, 2, 3]  
y = [1, 2, 3]  
print(x is y)  # False，因为它们是两个不同的对象  
print(x is not y)  # True

---

## 控制流

### 条件语句

x = 10  
if x > 5:  
    print("x 大于 5")  
elif x == 5:  
    print("x 等于 5")  
else:  
    print("x 小于 5")

### 循环语句

#### for 循环

for i in range(5):  # 从 0 到 4  
    print(i)

#### while 循环

i = 0  
while i < 5:  
    print(i)  
    i += 1

#### 循环控制语句

`break` 用于提前结束循环，`continue` 用于跳过当前循环，`pass` 用于占位。

# break  
for i in range(5):  
    if i == 3:  
        break  
    print(i)  
  
# continue  
for i in range(5):  
    if i == 3:  
        continue  
    print(i)  
  
# pass  
for i in range(5):  
    if i == 3:  
        pass  # 占位符  
    print(i)

---

## 函数

### 函数定义

def greet(name):  
    print(f"Hello, {name}")  
  
greet("Alice")

### 函数参数

def add(a, b=5):  
    return a + b  
  
print(add(10))  # 输出 15  
print(add(10, 3))  # 输出 13

### 返回值

def square(x):  
    return x * x  
  
result = square(4)  
print(result)  # 输出 16

### 匿名函数

sum = lambda a, b: a + b  
print(sum(2, 3))  # 输出 5

### 高阶函数

def apply_function(func, value):  
    return func(value)  
  
result = apply_function(lambda x: x * 2, 5)  
print(result)  # 输出 10

### 闭包

def outer(x):  
    def inner(y):  
        return x + y  
    return inner  
  
add_5 = outer(5)  
print(add_5(10))  # 输出 15

### 装饰器

def decorator(func):  
    def wrapper():  
        print("Before function")  
        func()  
        print("After function")  
    return wrapper  
  
@decorator  
def say_hello():  
    print("Hello!")  
  
say_hello()

---

## 模块与包

### 导入模块

import math  
print(math.sqrt(16))  # 输出 4.0

### 自定义模块

在同一目录下创建 `mymodule.py`，然后在主程序中导入并使用：

# mymodule.py  
def greet(name):  
    return f"Hello, {name}"

import mymodule  
print(mymodule.greet("Alice"))  # 输出 Hello, Alice

### 包的使用

包是一个包含多个模块的目录，包中包含一个 `__init__.py` 文件。可以通过 `import package.module` 方式来导入包中的模块。

---

## 类与对象

### 类定义

class Person:  
    def __init__(self, name, age):  
        self.name = name  
        self.age = age  
  
    def greet(self):  
        return f"Hello, {self.name}"  
  
p = Person("Alice", 25)  
print(p.greet())  # 输出 Hello, Alice

### 类的构造方法

class Person:  
    def __init__(self, name, age):  
        self.name = name  
        self.age = age  
  
p = Person("Alice", 25)

### 继承与多态

class Employee(Person):  
    def __init__(self, name, age, job):  
        super().__init__(name, age)  
        self.job = job  
  
    def greet(self):  
        return f"Hello, {self.name}, the {self.job}"  
  
e = Employee("Charlie", 28, "Engineer")  
print(e.greet())  # 输出 Hello, Charlie, the Engineer

### 类的特殊方法

class Person:  
    def __init__(self, name):  
        self.name = name  
  
    def __str__(self):  
        return f"Person(name={self.name})"  
  
p = Person("Alice")  
print(p)  # 输出 Person(name=Alice)

---

## 异常处理

### try-except 语句

try:  
    x = 1 / 0  
except ZeroDivisionError as e:  
    print("错误:", e)

### 自定义异常

class MyError(Exception):  
    pass  
  
try:  
    raise MyError("自定义异常")  
except MyError as e:  
    print(e)

### finally 语句

try:  
    x = 1 / 0  
except ZeroDivisionError:  
    print("捕获异常")  
finally:  
    print("无论如何都会执行")

---

## 文件操作

### 打开文件

file = open("example.txt", "w")  
file.write("Hello, World!")  
file.close()

### 读取文件

file = open("example.txt", "r")  
content = file.read()  
print(content)  
file.close()

### 写入文件

file = open("example.txt", "w")  
file.write("This is a new line")  
file.close()

### 文件操作上下文管理器

with open("example.txt", "r") as file:  
    content = file.read()  
    print(content)

---

## 常用标准库

### `os` 库

import os  
print(os.getcwd())  # 获取当前工作目录

### `sys` 库

import sys  
print(sys.argv)  # 获取命令行参数

### `math` 库

import math  
print(math.sqrt(16))  # 输出 4.0

### `datetime` 库

from datetime import datetime  
now = datetime.now()  
print(now)  # 输出当前日期时间

### `json` 库

import json  
data = {"name": "Alice", "age": 25}  
json_str = json.dumps(data)  
print(json_str)  # 输出 '{"name": "Alice", "age": 25}'

### `random` 库

import random  
print(random.randint(1, 10))  # 输出 1 到 10 之间的随机整数

### `re` 库（正则表达式）

import re  
pattern = r'\d+'  
result = re.match(pattern, "123abc")  
print(result.group())  # 输出 '123'

### `itertools` 库

import itertools  
perm = itertools.permutations([1, 2, 3], 2)  
print(list(perm))  # 输出 [(1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2)]