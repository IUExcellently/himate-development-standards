"""在任意发行开发副本中做只读静态校验。"""
import argparse
import ast
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

sys.dont_write_bytecode = True

from local_state import ROOT
from multica import summary
from release import allowed

LINK = re.compile(r"\]\(([^\s)]+)\)")
PRIVATE = re.compile(
    r"/Users/[A-Za-z0-9_.-]+/|/home/[A-Za-z0-9_.-]+/|[A-Za-z]:[\\/]Users[\\/]"
    r"|gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,}"
    r"|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
)


def validate(root):
    errors = []
    files = {}
    sources = [p for p in root.iterdir()
               if p.name in {"README.md", "SKILL.md", "manifest.json", "INSTALL.md", "CHANGELOG.md",
                             "scripts", "standards", "references", "integrations", "examples",
                             "tests", "config", "reports", ".github"}]
    for source in sources:
        for path in ([source] if source.is_file() else source.rglob("*")):
            if path.is_symlink():
                errors.append(f"发行文件包含链接：{path.relative_to(root)}")
                continue
            if not path.is_file() or path.suffix not in {".md", ".py", ".json", ".yml", ".yaml"}:
                continue
            name = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            if allowed(name):
                files[name] = text.encode("utf-8")
            if path.suffix == ".py":
                ast.parse(text, filename=name)
            if PRIVATE.search(text):
                errors.append(f"检测到机器路径或敏感内容样式：{name}")
            if path.suffix == ".md":
                for target in LINK.findall(text):
                    if "://" in target or target.startswith("#"):
                        continue
                    candidate = (path.parent / unquote(target.split("#")[0])).resolve()
                    if root not in candidate.parents or not candidate.exists():
                        errors.append(f"无效本地链接：{name} -> {target}")
    multica = summary(files)
    version = multica["version"]
    if not (root / "CHANGELOG.md").read_text(encoding="utf-8").startswith(f"# 版本说明\n\n## {version}\n"):
        errors.append("manifest 与 CHANGELOG 版本不一致")
    return {"ok": not errors, "version": version, "release_files": len(files), "multica_bundle": multica, "errors": errors}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    result = validate(Path(args.root).resolve(strict=True))
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(not result["ok"])
