import argparse
from pathlib import Path

from compiler.submission_export import generate_submission_package


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate course submission test files.")
    parser.add_argument(
        "--input",
        default="全部测试程序/01编译器测试用例",
        help="Directory containing test*.txt source files.",
    )
    parser.add_argument(
        "--output",
        default="提交测试文件",
        help="Directory to receive test*.txt, test*.int and test*.doc files.",
    )
    args = parser.parse_args()

    generated = generate_submission_package(Path(args.input), Path(args.output))
    print(f"generated {len(generated)} test cases into {args.output}")
    for item in generated:
        print(f"- {item.stem}: {item.txt_path.name}, {item.int_path.name}, {item.doc_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
