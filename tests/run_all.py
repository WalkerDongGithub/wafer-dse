"""运行所有 .md 测试文件中的 Python 代码块.

用法:  cd tests && PYTHONPATH=../src python3 run_all.py
"""

import re
import sys
import subprocess
from pathlib import Path


def extract_code_blocks(md_path: Path) -> str:
    """从 markdown 文件中提取所有 Python 代码块."""
    text = md_path.read_text()
    blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    return "\n".join(blocks)


def main():
    tests_dir = Path(__file__).parent
    md_files = sorted(tests_dir.rglob("*.md"))
    if not md_files:
        print("No .md test files found.")
        sys.exit(1)

    passed, failed = 0, 0
    for md_file in md_files:
        code = extract_code_blocks(md_file)
        if not code:
            continue

        # 写入临时文件, 注入 sys.path
        full_code = (
            "import sys; sys.path.insert(0, '../src')\n"
            + code
        )
        tmp = Path("/tmp/_test_suite.py")
        tmp.write_text(full_code)

        r = subprocess.run(
            [sys.executable, str(tmp)],
            capture_output=True, text=True,
        )

        rel = md_file.relative_to(tests_dir)
        if r.returncode == 0:
            passed += 1
            print(f"  OK  {rel}")
        else:
            failed += 1
            # 只打印最后几行错误
            err_lines = r.stderr.strip().split("\n")
            last = err_lines[-1] if err_lines else "(no output)"
            print(f"  FAIL  {rel}  —  {last}")

    print(f"\n{'='*50}")
    print(f"  {passed + failed} files,  {passed} passed,  {failed} failed")
    print(f"{'='*50}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
