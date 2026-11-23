"""运行安装、隔离、动态路由和只读快照的统一静态验证。"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import tempfile

from detect_project import MANIFEST, ROOT, detect
from install_global import build_plan
from resolve_conflict import decide
from resolve_rules import resolve
from snapshot import capture
from status import platform_status


def compare(before, after):
    a, b = before["entries"], after["entries"]
    changed = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
    return {
        "branch_head_status_same": all(before[k] == after[k] for k in ("root", "head", "status")),
        "git_metadata_same": before["git_metadata"] == after["git_metadata"],
        "tracked_changes": [k for k in changed if any(x and x[0] == "tracked" for x in (a.get(k), b.get(k)))],
        "untracked_ignored_changes": [k for k in changed if all(not x or x[0] != "tracked" for x in (a.get(k), b.get(k)))],
        "ai_changes": [k for k in changed if any(x and x[1] for x in (a.get(k), b.get(k)))],
        "new_cache_or_temp": [k for k in b.keys() - a.keys() if re.search(r"cache|(^|/)tmp/|\.pyc$", k, re.I)],
        "counts": dict(Counter(v[0] for v in b.values())),
        "ai_entries": sum(v[1] for v in b.values()),
        "trellis_present": ".trellis/workflow.md" in b,
    }


def run():
    repo = Path(MANIFEST["project"]["roots"][0])
    checks = {}

    def check(name, value):
        checks[name] = bool(value)

    docs = set(MANIFEST["base"]) | {p for paths in MANIFEST["tags"].values() for p in paths}
    check("manifest_is_canonical", str(ROOT) == MANIFEST["root"])
    for where in ("SKILL.md", "integrations/codex/SKILL.md", "integrations/claude/SKILL.md",
                  "integrations/qoder/SKILL.md"):
        body = (ROOT / where).read_text(encoding="utf-8")
        checks[f"skill_metadata:{where}"] = bool(re.match(
            r"^---\nname: himate-development-standards\ndescription: [^\n]+\n---\n", body
        ))
    check("twelve_backend_rules", len(MANIFEST["backend"]) == 12
          and set(MANIFEST["backend"]) == {str(p.relative_to(ROOT)) for p in (ROOT / "standards/backend").glob("*.md")}
          and set(MANIFEST["backend"]) <= docs)
    check("rule_files_reachable", all((ROOT / p).is_file() and (ROOT / p).resolve().is_relative_to(ROOT) for p in docs))
    markdown_files = list(ROOT.glob("standards/**/*.md")) + list(ROOT.glob("references/*.md")) + [ROOT / "README.md", ROOT / "SKILL.md"]
    check("local_markdown_links", all(
        (path.parent / link.split("#")[0]).is_file()
        for path in markdown_files
        for link in re.findall(r"\]\(([^ ):]+\.md(?:#[^ )]+)?)\)", path.read_text(encoding="utf-8"))
    ))
    check("project_root_and_nested", detect(repo)["active"] and detect(repo / "backend")["active"])
    # 临时样本位于外部规范目录，退出时自动清理。
    with tempfile.TemporaryDirectory(prefix=".validate-", dir=ROOT) as tmp:
        tmp = Path(tmp)
        link = tmp / "same-project"
        link.symlink_to(repo, target_is_directory=True)
        check("symlink_to_registered_workspace", detect(link)["active"])
        outsider = tmp / "himate"
        outsider.mkdir()
        subprocess.run(["git", "-C", str(outsider), "init", "-q"], check=True, timeout=10)
        for name in MANIFEST["project"]["signatures"]:
            path = outsider / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((repo / name).read_bytes())
        check("E_unregistered_lookalike_git_repo", not detect(outsider)["active"]
              and not resolve(outsider, "Java SQL SSE")["rules"])
        check("outside_target_is_ignored", not (set(resolve(repo, paths=[str(outsider / "backend/a.java")])["tags"]) & {"java", "sql"}))

    def matched(task="", *paths, tags=(), loaded=()):
        return set(resolve(repo, task, paths, tags, loaded)["rules"])

    def backend(n):
        return MANIFEST["backend"][n - 1]

    check("A_trellis_real_conflict_requires_user", decide(material=True) == "request-user-decision"
          and decide(material=False) == "apply-together-or-follow-existing-decision")
    check("B_dependency_approval", decide(dependency_change=True) == "request-dependency-approval"
          and "standards/dependency-policy.md" in matched("新增依赖", "frontend/pnpm-lock.yaml"))
    css = matched("弹窗局部样式", "frontend/apps/admin/src/styles/global.css")
    check("C_css_is_scoped_route", "standards/frontend-styles.md" in css and not (css & set(MANIFEST["backend"])))
    check("D_version_rules_and_migration", decide(security_override=True, material=True) == "apply-version-matched-security-rule"
          and decide(security_override=True, migration=True) == "request-change-authorization")
    controller = matched("", "backend/x/src/main/java/controller/DemoController.java")
    check("controller_api_security", {backend(1), backend(3), backend(10), "standards/api-contracts.md"} <= controller and backend(7) not in controller)
    sql = matched("", "backend/x/src/main/resources/mapper/ItemMapper.xml", "backend/sql/migration/new.sql")
    check("sql_and_schema", {backend(4), backend(5), backend(6), backend(10)} <= sql and backend(7) not in sql)
    check("pool_and_transaction", {backend(4), backend(7), backend(11), backend(12)} <= matched("调优 Hikari", "backend/x/src/main/resources/application-prod.yml"))
    check("mixed_script_hikari_kafka", {backend(7), backend(9)} <=
          matched("调整HikariCP配置并优化Kafka消费者幂等", "backend/x/src/main/resources/application-prod.yml"))
    check("scoped_java_review", backend(12) in matched("审查变更", "backend/x/Demo.java"))
    check("service_writes", backend(4) in matched("更新状态", "backend/x/service/ExampleService.java") and backend(4) not in matched("校对说明", "backend/x/service/ExampleService.java"))
    check("kafka_and_concurrency", {backend(4), backend(8), backend(9)} <= matched("Kafka 线程池", "backend/x/kafka/ExampleConsumer.java"))
    check("python_redis_is_not_java", not (matched("调度器 Redis", "himate-dispatcher/app/infra/redis_client.py") & set(MANIFEST["backend"])))
    cross = matched("联动修改 SSE", "frontend/packages/chat-transport/src/main.ts",
                    "himate-dispatcher/app/api/routes/dispatch.py", "backend/x/sse/Events.java",
                    loaded=["standards/core.md"])
    check("cross_layer_and_dedup", {"standards/frontend.md", "standards/python-dispatcher.md",
          "standards/api-contracts.md", backend(1)} <= cross and "standards/core.md" not in cross)
    routed = resolve(repo, "SSE", ["frontend/packages/chat-transport/src/main.ts"] * 2)
    check("repeated_path_no_duplicate", len(routed["rules"]) == len(set(routed["rules"])))

    platforms = platform_status()
    check("G_static_user_level_install", all(p.get("installed") for p in platforms.values()))
    check("install_is_idempotent", all(not build_plan(p, False) for p in platforms))
    check("uninstall_is_planned", all(len(build_plan(p, True)) >= 3 for p in platforms))

    before = json.loads((ROOT / "reports" / "baseline-before.json").read_text(encoding="utf-8"))
    after = capture(repo)
    verification = compare(before, after)
    check("F_repository_and_original_trellis_unchanged", verification["branch_head_status_same"]
          and verification["git_metadata_same"] and verification["trellis_present"]
          and not any(verification[key] for key in ("tracked_changes", "untracked_ignored_changes",
                                                     "ai_changes", "new_cache_or_temp")))
    return {"ok": all(checks.values()), "checks": checks, "baseline": verification,
            "platforms": platforms}, after


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="将快照与结果写入外部报告目录")
    args = parser.parse_args()
    result, snapshot = run()
    if args.record:
        for name, data in (("baseline-after.json", snapshot), ("validation-results.json", result)):
            path = ROOT / "reports" / name
            if path.resolve() != path or (path.exists() and path.stat().st_nlink != 1):
                parser.exit(1, "报告路径不安全\n")
            path.write_text(json.dumps(data, ensure_ascii=True, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)
