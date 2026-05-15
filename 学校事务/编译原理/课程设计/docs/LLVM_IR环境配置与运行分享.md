# LLVM IR 环境配置与运行流程分享

## 1. 分享目标

本次分享主要说明：在 Windows 上如何配置可以编译 LLVM IR 的环境，以及如何使用 `x64 Native Tools Command Prompt for VS` 运行本项目导出的 `outputs/llvm_ir.ll`。

需要先说明一点：`x64 Native Tools Command Prompt for VS` 不是单独下载的软件。它是安装 Visual Studio 或 Visual Studio Build Tools 的 C++ 编译工具后自动提供的开发者命令行入口。普通 PowerShell 或 CMD 不一定能直接找到 `cl`、`link`、`clang`、Windows SDK 等工具，而这个命令行会提前配置好 `PATH`、`INCLUDE`、`LIB` 等环境变量。

## 2. 下载入口

打开 Visual Studio 官方下载页：

[https://visualstudio.microsoft.com/downloads](https://visualstudio.microsoft.com/downloads)

推荐两种安装方式：

| 方式 | 适合情况 | 说明 |
| --- | --- | --- |
| Visual Studio Community | 希望同时安装完整 IDE | 免费版本，安装体积较大 |
| Build Tools for Visual Studio | 只需要命令行编译工具 | 更轻量，适合本项目验证 LLVM IR |

本项目只需要编译和链接工具，因此推荐下载 **Build Tools for Visual Studio**。下载后会得到类似 `vs_BuildTools.exe` 的安装程序。

## 3. 安装时勾选哪些

运行安装程序后，进入 Visual Studio Installer。

在“工作负载”页面勾选：

- `Desktop development with C++`

如果界面显示为中文，一般叫：

- `使用 C++ 的桌面开发`

这个工作负载会安装 MSVC、MSBuild、Windows SDK、C++ 运行库等基础组件。微软官方的 Build Tools 组件说明中，这个工作负载的 ID 是 `Microsoft.VisualStudio.Workload.VCTools`，用途是构建 Windows C++ 程序。

然后在右侧或“单个组件”中确认以下组件：

| 组件 | 是否建议 | 作用 |
| --- | --- | --- |
| MSVC Build Tools for x64/x86 | 必选 | 提供 `cl.exe`、`link.exe` 等 MSVC 编译链接工具 |
| Windows 10/11 SDK | 必选 | 提供 Windows 头文件、库文件和运行时支持 |
| C++ CMake tools for Windows | 可选 | 本项目不依赖，但很多 C/C++ 项目会用到 |
| C++ Clang Compiler for Windows | 建议勾选 | 提供 Visual Studio 集成的 Clang/LLVM 编译器 |

本项目验证 LLVM IR 时最关键的是 `clang`。如果不勾选 `C++ Clang Compiler for Windows`，也可以单独安装 LLVM 官方工具链，但为了课堂演示流程统一，建议直接在 Visual Studio Installer 里勾选该组件。

安装完成后，重启终端或直接从开始菜单打开开发者命令行。

## 4. 打开 x64 Native Tools Command Prompt

安装完成后，按下面步骤打开：

1. 点击 Windows 开始菜单。
2. 搜索 `x64 Native Tools Command Prompt`。
3. 选择类似下面的入口：

```text
x64 Native Tools Command Prompt for VS 2022
```

如果安装的是更新版本，名称可能是：

```text
x64 Native Tools Command Prompt for VS 2026
```

打开后，先检查工具是否可用：

```cmd
where cl
where link
where clang
```

正常情况下会输出对应的 `.exe` 路径。例如：

```text
C:\Program Files\Microsoft Visual Studio\...\VC\Tools\MSVC\...\bin\Hostx64\x64\cl.exe
C:\Program Files\Microsoft Visual Studio\...\VC\Tools\MSVC\...\bin\Hostx64\x64\link.exe
C:\Program Files\Microsoft Visual Studio\...\VC\Tools\Llvm\bin\clang.exe
```

如果 `where clang` 找不到结果，通常说明安装时没有勾选 `C++ Clang Compiler for Windows`，需要重新打开 Visual Studio Installer 修改安装。

## 5. 进入课程设计项目目录

在 `x64 Native Tools Command Prompt for VS` 中进入项目目录：

```cmd
cd /d "D:\path\to\课程设计"
```

这里的 `/d` 用于在 CMD 中切换盘符。如果项目在 D 盘，从 C 盘命令行进入 D 盘目录时必须加 `/d`。实际使用时把 `D:\path\to\课程设计` 替换成自己的项目目录。

## 6. 先由项目生成 LLVM IR

项目中的 LLVM IR 文件由编译器流水线导出，位置是：

```text
outputs\llvm_ir.ll
```

可以通过 GUI 生成：

1. 运行项目：

```powershell
python app.py
```

如果本机 Python 没配好，也可以使用项目环境中的 Python：

```powershell
& "C:\path\to\python.exe" app.py
```

2. 打开或粘贴测试程序，例如：

```text
examples\系统测试用例\07_LLVM_IR生成\llvm_branch_call.c
```

3. 点击 `运行`。
4. 在右侧查看 `LLVM IR` 和 `LLVM Verify`。
5. 点击 `导出`，生成 `outputs\llvm_ir.ll`。

也可以直接运行系统测试，确认 LLVM IR 相关功能没有问题：

```powershell
python examples\系统测试用例\run_system_tests.py
```

预期输出包含：

```text
system tests: PASS
covered: lexical, syntax, semantic, IR/interpreter, MASM16, log regex NFA/DFA, LLVM IR, CFG/DAG, GUI editor inputs
```

## 7. 用 clang 验证 LLVM IR 能否编译

在 `x64 Native Tools Command Prompt for VS` 中执行：

```cmd
clang -c outputs\llvm_ir.ll -o outputs\llvm_ir.obj
```

这一步只编译，不链接。它的作用是验证 `outputs\llvm_ir.ll` 是否能被 LLVM 前端接受，并生成目标文件 `outputs\llvm_ir.obj`。

如果输出类似：

```text
warning: overriding the module target triple with x86_64-pc-windows-msvc... [-Woverride-module]
1 warning generated.
```

这是 warning，不是 error。只要命令退出成功，并且生成了 `outputs\llvm_ir.obj`，就说明 IR 至少通过了外部编译验证。

## 8. 编译成 exe 并运行

如果要进一步验证能否链接并运行，执行：

```cmd
clang outputs\llvm_ir.ll -o outputs\llvm_ir.exe
```

然后运行：

```cmd
outputs\llvm_ir.exe
```

如果源程序里有 `write(...)`，运行时会在命令行输出对应数字。例如 `llvm_branch_call.c` 的逻辑是：

```c
int square(int x) {
    return x * x;
}

main() {
    int a;
    int b;
    a = 4;
    b = square(a);
    if (b > 10) {
        write(b);
    } else {
        write(0);
    }
}
```

当前项目的 LLVM IR 后端对用户自定义函数调用采用简化处理，重点是验证 IR 结构、分支、变量读写和外部编译流程。因此课堂分享时可以强调：本项目的 4.2 任务目标是“四元式到 LLVM IR 风格代码的简化转换器”，不是完整 C 编译器后端。

## 9. 项目里的 LLVM Verify 怎么看

项目会同时生成：

```text
outputs\llvm_verify.txt
```

示例结果：

```text
LLVM Verify
Internal verifier: PASS
External tools:
- llvm-as: not found
- lli: not found
Manual commands:
  llvm-as outputs/llvm_ir.ll -o outputs/llvm_ir.bc
  lli outputs/llvm_ir.ll
  clang -c outputs/llvm_ir.ll -o outputs/llvm_ir.obj
  clang outputs/llvm_ir.ll -o outputs/llvm_ir.exe
  outputs\llvm_ir.exe
- clang -c: PASS
warning: overriding the module target triple with x86_64-pc-windows-msvc... [-Woverride-module]
1 warning generated.
```

重点解读：

| 输出 | 含义 |
| --- | --- |
| `Internal verifier: PASS` | 项目内部检查通过，包括 `main`、label、基本块终结符、`ret` 等 |
| `llvm-as: not found` | 没安装完整 LLVM 工具链，不影响使用 `clang` 验证 |
| `lli: not found` | 没安装 LLVM 解释执行工具，不影响 `clang -c` |
| `clang -c: PASS` | LLVM IR 已经能被 Clang 编译成目标文件 |
| `warning ... target triple` | 目标平台提示，一般不是错误 |

## 10. 常见问题

### 问题 1：开始菜单搜不到 x64 Native Tools Command Prompt

可能原因：

- 没有安装 Visual Studio 或 Build Tools。
- 安装时没有勾选 `Desktop development with C++` / `使用 C++ 的桌面开发`。
- 安装后开始菜单索引还没刷新。

解决方式：

1. 打开 Visual Studio Installer。
2. 找到已安装的 Build Tools 或 Visual Studio。
3. 点击 `Modify` / `修改`。
4. 勾选 `Desktop development with C++`。
5. 确认安装后重新搜索。

### 问题 2：`where clang` 找不到

说明 Clang 没有被安装到当前 VS 工具环境中。

解决方式：

1. 打开 Visual Studio Installer。
2. 点击 `Modify` / `修改`。
3. 进入“单个组件”。
4. 搜索并勾选 `C++ Clang Compiler for Windows`。
5. 安装完成后重新打开 `x64 Native Tools Command Prompt for VS`。

### 问题 3：普通 PowerShell 中能不能运行

可以，但不推荐作为首次演示环境。普通 PowerShell 通常没有自动设置 MSVC 和 Windows SDK 的环境变量，可能出现 `link.exe` 找不到、库文件找不到等问题。

如果一定要在普通命令行中使用，需要先手动调用 Visual Studio 的环境脚本，例如：

```cmd
"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

不同版本和安装位置路径可能不同，所以课堂分享时直接使用 `x64 Native Tools Command Prompt for VS` 更稳定。

### 问题 4：`clang -c` 成功，但 `clang ... -o exe` 失败

`clang -c` 只生成 `.obj`，不需要完整链接。生成 `.exe` 时需要链接器和运行库。如果链接失败，优先检查：

```cmd
where link
where cl
where clang
```

如果 `link` 或 `cl` 找不到，说明没有进入开发者命令行，或者 C++ Build Tools 没安装完整。

## 11. 课堂演示流程建议

可以按下面顺序讲：

1. 先说明为什么要配置 VS C++ Build Tools：Windows 上链接本机程序需要 MSVC、Windows SDK 和运行库。
2. 打开 Visual Studio 下载页，展示 Build Tools 下载入口。
3. 展示安装器中勾选 `Desktop development with C++`。
4. 强调额外勾选 `C++ Clang Compiler for Windows`。
5. 打开 `x64 Native Tools Command Prompt for VS`。
6. 运行 `where cl`、`where link`、`where clang` 检查环境。
7. 进入课程设计项目目录。
8. 展示 `outputs\llvm_ir.ll`。
9. 执行 `clang -c outputs\llvm_ir.ll -o outputs\llvm_ir.obj`。
10. 执行 `clang outputs\llvm_ir.ll -o outputs\llvm_ir.exe` 和 `outputs\llvm_ir.exe`。
11. 最后展示 `outputs\llvm_verify.txt`，说明内部验证和外部验证分别证明了什么。

## 12. 一页命令速查

```cmd
cd /d "D:\path\to\课程设计"

where cl
where link
where clang

clang -c outputs\llvm_ir.ll -o outputs\llvm_ir.obj
clang outputs\llvm_ir.ll -o outputs\llvm_ir.exe
outputs\llvm_ir.exe
```

## 13. 参考资料

- Visual Studio 官方下载页：[https://visualstudio.microsoft.com/downloads](https://visualstudio.microsoft.com/downloads)
- Microsoft Learn：Build Tools 工作负载与组件 ID：[https://learn.microsoft.com/en-us/visualstudio/install/workload-component-id-vs-build-tools](https://learn.microsoft.com/en-us/visualstudio/install/workload-component-id-vs-build-tools)
- Microsoft Learn：命令行使用 C++ Build Tools：[https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line)
- Microsoft Learn：Visual Studio 中的 Clang/LLVM 支持：[https://learn.microsoft.com/en-us/cpp/build/clang-support-cmake](https://learn.microsoft.com/en-us/cpp/build/clang-support-cmake)
