"""列出本地登记、安装文件和本轮路由；不声称客户端已执行。"""
import argparse
import json

from detect_project import ROOT
from install_global import PLATFORMS, current, digest, entries, load_receipt, safe_path, HOME
from resolve_rules import resolve, route_arguments


def platform_status():
    result = {}
    for platform in PLATFORMS:
        try:
            receipt = load_receipt(platform)
            expected = {str(path) for path, _, _ in entries(platform)}
            checks = {}
            for name, info in receipt["files"].items():
                if name not in expected:
                    checks[name] = False
                    continue
                path = next(p for p, _, _ in entries(platform) if str(p) == name)
                safe_path(path, HOME)
                checks[name] = digest(current(path)[0]) == info["installed_sha256"]
            result[platform] = {
                "installed": receipt["installed"] and set(checks) == expected and all(checks.values()),
                "expected_paths": sorted(expected), "file_checks": checks,
            }
        except (OSError, ValueError, KeyError) as exc:
            result[platform] = {"installed": False, "error": str(exc)}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    route_arguments(parser)
    args = parser.parse_args()
    routed = resolve(args.cwd, args.task, args.path, args.tag, args.loaded)
    state = ROOT / "reports" / "validation-results.json"
    status = {"platforms": platform_status(), "routing": routed,
              "conflicts": {
                  "status": "由当前会话判断",
                  "analysis": str(ROOT / "references" / "conflict-analysis.md"),
                  "decision_log": (str(ROOT / "reports" / "decisions.md")
                                   if (ROOT / "reports" / "decisions.md").is_file() else None)},
              "validation": json.loads(state.read_text(encoding="utf-8")) if state.is_file() else None}
    print(json.dumps(status, ensure_ascii=False, indent=2))
