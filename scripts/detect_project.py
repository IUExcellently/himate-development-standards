"""先核对登记位置，再只读验证 Git 和项目指纹。"""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def detect(cwd):
    result = {"active": False, "root": None}
    try:
        here = Path(cwd).expanduser().resolve(strict=True)
        if not here.is_dir():
            return dict(result, reason="cwd-not-directory")
        registered = next((Path(p) for p in MANIFEST["project"]["roots"]
                           if Path(p) == here or Path(p) in here.parents), None)
        if not registered:
            return dict(result, reason="unregistered-location")
        env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"}
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
                    "GIT_CEILING_DIRECTORIES"):
            env.pop(key, None)
        value = subprocess.check_output(
            ["git", "-c", "core.fsmonitor=false", "-C", str(here), "rev-parse", "--show-toplevel"],
            env=env, stderr=subprocess.DEVNULL, timeout=5,
        )
        if Path(os.fsdecode(value).rstrip("\n")).resolve(strict=True) != registered:
            return dict(result, reason="different-git-root")
        for name, markers in MANIFEST["project"]["signatures"].items():
            path = (registered / name).resolve(strict=True)
            if registered not in path.parents or not path.is_file():
                return dict(result, reason="signature-outside-root")
            with path.open(encoding="utf-8") as stream:
                body = stream.read(256 * 1024)
            if not all(marker in body for marker in markers):
                return dict(result, reason=f"signature-mismatch:{name}")
        return {"active": True, "root": str(registered), "reason": "git-root-and-signatures"}
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        return dict(result, reason="workspace-unavailable")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=".")
    print(json.dumps(detect(parser.parse_args().cwd), ensure_ascii=False))
