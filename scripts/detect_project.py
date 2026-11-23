"""先查私有登记，再验证真实 Git 根和公开结构指纹。"""
import sys

if __name__ == "__main__":
    sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess

from git_access import git_root
from local_state import Local, ROOT

MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
SIGNATURE_LIMIT = 256 * 1024


class InvalidSignatures(ValueError):
    pass


def project_signatures(manifest):
    project = manifest.get("project")
    signatures = project.get("signatures") if isinstance(project, dict) else None
    if not isinstance(signatures, dict) or not signatures:
        raise InvalidSignatures("发行清单缺少有效的项目指纹")
    for name, markers in signatures.items():
        if not isinstance(name, str) or not name or any(c in name for c in ("\\", ":", "\0")):
            raise InvalidSignatures("项目指纹路径无效")
        relative = PurePosixPath(name)
        if (relative.is_absolute() or relative == PurePosixPath(".")
                or relative.as_posix() != name or ".." in relative.parts):
            raise InvalidSignatures("项目指纹路径必须位于工作树内")
        if not isinstance(markers, list) or not markers or not all(
            isinstance(marker, str) and marker.strip() and len(marker) <= SIGNATURE_LIMIT for marker in markers
        ):
            raise InvalidSignatures(f"项目指纹标记无效：{name}")
    return signatures


def signature_checks(root):
    for name, markers in project_signatures(MANIFEST).items():
        check = {"path": name}
        try:
            path = (root / name).resolve()
            if root not in path.parents:
                yield dict(check, status="outside-root")
                continue
            if not path.exists():
                yield dict(check, status="missing")
                continue
            if not path.is_file():
                yield dict(check, status="not-a-file")
                continue
            with path.open(encoding="utf-8") as stream:
                body = stream.read(SIGNATURE_LIMIT)
        except (OSError, RuntimeError, ValueError):
            yield dict(check, status="unreadable")
            continue
        missing = [marker for marker in markers if marker not in body]
        if missing:
            status = "scan-limit" if len(body) == SIGNATURE_LIMIT else "marker-mismatch"
            yield dict(check, status=status, missing_markers=missing)
        else:
            yield dict(check, status="matched")


def signature_problem(check):
    if check["status"] == "outside-root":
        return "signature-outside-root"
    if check["status"] == "marker-mismatch":
        return "signature-mismatch:" + check["path"]
    return "signature-" + check["status"] + ":" + check["path"]


def verify_root(root):
    if git_root(root) != root:
        return "different-git-root"
    return next((signature_problem(c) for c in signature_checks(root) if c["status"] != "matched"), None)


def detect(cwd, local=None, *, diagnose=False):
    result = {"active": False, "root": None}
    try:
        here = Path(cwd).expanduser().resolve(strict=True)
        if not here.is_dir():
            return dict(result, reason="cwd-not-directory")
        roots = [Path(p) for p in (local or Local()).registrations()["roots"]]
        candidates = [p for p in roots if p == here or p in here.parents]
        if not candidates:
            return dict(result, reason="unregistered-location")
        registered = max(candidates, key=lambda p: len(p.parts))
        if git_root(here) != registered:
            return dict(result, reason="different-git-root")
        checks = signature_checks(registered)
        if diagnose:
            result["signatures"] = list(checks)
            checks = result["signatures"]
        problem = next((signature_problem(c) for c in checks if c["status"] != "matched"), None)
        if problem:
            return dict(result, reason=problem)
        return dict(result, active=True, root=str(registered), reason="git-root-and-signatures")
    except InvalidSignatures:
        return dict(result, reason="invalid-signatures")
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        return dict(result, reason="workspace-unavailable")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--home", help="独立的测试用户目录")
    parser.add_argument("--diagnose", action="store_true", help="列出已登记 Git 根的指纹结果")
    args = parser.parse_args()
    print(json.dumps(detect(args.cwd, Local(args.home), diagnose=args.diagnose)))
