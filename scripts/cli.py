"""用户级生命周期入口，默认只输出计划。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
if sys.version_info < (3, 10):
    sys.exit("需要 Python 3.10 或更高版本")

from detect_project import MANIFEST, detect, verify_root
from git_access import git_root
from integrations import PLATFORMS, detected, entry, environment, wrapper
from legacy import merge_registration, remove_legacy
from local_state import Local, ROOT, digest, encode, inside, read, read_json, user_lock
from release import TEMPLATE, bundle_path, recorded_release, release_changes, reviewed_source
from transactions import Plan, apply_plan, journal_changes, recover


def installation(local):
    inside(local.receipt, local.home)
    receipt = read_json(local.receipt, {"schema": 1, "revision": None, "version": None, "platforms": {}})
    if receipt.get("schema") != 1 or not isinstance(receipt.get("platforms"), dict):
        raise ValueError("安装回执格式无效")
    for platform, record in receipt["platforms"].items():
        if platform not in PLATFORMS or str(entry(local, platform)) != record["path"]:
            raise ValueError(f"用户配置落点已变化：{platform}")
    return receipt


def status(local):
    receipt = installation(local)
    platforms = {}
    for name in PLATFORMS:
        path = entry(local, name)
        record = receipt["platforms"].get(name)
        try:
            inside(path, local.home)
            file = read(path)
            platforms[name] = {"path": str(path), "registered": record is not None,
                               "file_present": file is not None,
                               "matches_receipt": bool(record and file is not None and digest(file) == record["sha256"])}
        except (OSError, ValueError) as exc:
            platforms[name] = {"path": str(path), "registered": record is not None, "error": str(exc)}
    healthy = None
    if receipt["revision"]:
        recorded_release(local, receipt["revision"])
        healthy = True
    raw, _ = journal_changes(local)
    return {"version": MANIFEST["version"], "active_release": receipt["revision"],
            "installed_version": receipt["version"], "verified_bundle": healthy,
            "pending_recovery": raw is not None, "platforms": platforms,
            "projects": local.registrations()["roots"]}


def entry_changes(local, plan, receipt, wanted, payload):
    mapping = {}
    for platform in PLATFORMS:
        prior = receipt["platforms"].get(platform)
        if not prior and platform not in wanted:
            continue
        path = entry(local, platform)
        inside(path, local.home)
        before = read(path)
        staged = plan.changes.get(path)
        effective = staged.after if staged else before
        if prior:
            if before is not None and digest(before) != prior["sha256"]:
                plan.conflicts.append(f"用户入口已修改：{path}")
                continue
        elif effective is not None or (not staged and path.parent.is_dir() and any(path.parent.iterdir())):
            plan.conflicts.append(f"存在未经确认的同名 Skill：{path.parent}")
            continue
        after = payload if platform in wanted else None
        plan.add(path, effective, after)
        if after is not None:
            mapping[platform] = {"path": str(path), "sha256": digest(after)}
    return mapping


def lifecycle(local, args):
    receipt = installation(local)
    plan = Plan(local, migration=bool(getattr(args, "legacy", None)))
    installed = set(receipt["platforms"])
    operation = args.command
    if operation == "uninstall":
        wanted = installed - set(args.platform or installed)
        # 部分卸载保持未选中的入口原字节和回执。
        if not installed - wanted:
            return plan
        for platform in installed - wanted:
            path = entry(local, platform)
            inside(path, local.home)
            before = read(path)
            if before is not None and digest(before) != receipt["platforms"][platform]["sha256"]:
                plan.conflicts.append(f"用户入口已修改：{path}")
            else:
                plan.add(path, before, None)
        updated = receipt.copy()
        updated["last_uninstall"] = {"revision": receipt["revision"], "platforms": sorted(installed - wanted)}
        updated["platforms"] = {p: receipt["platforms"][p] for p in wanted}
        if not wanted:
            updated.update(revision=None, version=None)
        plan.add(local.receipt, read(local.receipt), encode(updated))
        return plan

    if operation == "rollback":
        wanted = installed.copy()
        revision = args.to
        if args.restore_uninstalled:
            removed = receipt.get("last_uninstall", {})
            if removed.get("revision") != revision or not removed.get("platforms"):
                raise ValueError("没有与目标版本相符的最近卸载记录")
            if not set(removed["platforms"]) <= PLATFORMS.keys():
                raise ValueError("卸载记录的平台无效")
            wanted.update(removed["platforms"])
        if not wanted:
            raise ValueError("没有已安装平台可切换。恢复最近卸载使用 --restore-uninstalled")
        version, files = recorded_release(local, revision)
        bundle = bundle_path(local, revision)
    else:
        if operation == "update" and not installed and not args.legacy:
            raise ValueError("没有现有安装。请执行 install")
        wanted = installed | set(args.platform or ())
        if not wanted:
            wanted = {p for p, found in detected(local).items() if found}
        if not wanted:
            raise ValueError("未检测到客户端，请显式指定 --platform")
        revision = args.revision
        version, files = reviewed_source(args.source, revision)
        if installed and revision != receipt["revision"]:
            previous_version = tuple(map(int, receipt["version"].split(".")))
            if operation != "update":
                raise ValueError("已有其他版本，请执行 update")
            if tuple(map(int, version.split("."))) <= previous_version:
                raise ValueError("更新需要更高的 SemVer。旧版本请使用 rollback")
        if args.legacy:
            folder = Path(args.legacy).expanduser().resolve(strict=True)
            merge_registration(local, folder, plan)
        # 同时检查活跃的 V2 引导，防止 V2 和 V3 在会话内重复加载。
        remove_legacy(local, folder if args.legacy else local.state / "no-legacy-receipts", plan, wanted)
        if args.legacy and plan.conflicts:
            return plan
        bundle = release_changes(local, revision, files, plan.add)
    mapping = entry_changes(local, plan, receipt, wanted, wrapper(bundle, files[TEMPLATE]))
    updated = {**receipt, "version": version, "revision": revision, "platforms": mapping}
    if operation == "rollback" and args.restore_uninstalled:
        updated.pop("last_uninstall", None)
    plan.add(local.receipt, read(local.receipt), encode(updated))
    return plan


def project_plan(local, args):
    plan = Plan(local)
    if args.command == "migrate":
        merge_registration(local, Path(args.legacy).expanduser().resolve(strict=True), plan)
        return plan
    data = local.registrations()
    if args.command == "register":
        root = git_root(Path(args.path).expanduser().resolve(strict=True))
        problem = verify_root(root)
        if problem:
            raise ValueError(f"项目指纹不匹配：{problem}")
        data["roots"] = list(dict.fromkeys([*data["roots"], str(root)]))
    else:
        root = Path(args.path).expanduser().resolve()
        data["roots"] = [item for item in data["roots"] if Path(item) != root]
    original = read(local.registry)
    if original is not None or data["roots"]:
        plan.add(local.registry, original, encode(data))
    return plan


def parser():
    cli = argparse.ArgumentParser(description="HiMate 用户级 Skill 生命周期")
    commands = cli.add_subparsers(dest="command", required=True)
    for action in ("install", "update", "uninstall", "rollback", "recover", "doctor",
                   "status", "list", "register", "unregister", "migrate"):
        sub = commands.add_parser(action)
        sub.add_argument("--home", help="隔离测试使用的用户目录，须已存在")
        if action in {"install", "update", "uninstall"}:
            sub.add_argument("--platform", action="append", choices=PLATFORMS)
        if action in {"install", "update"}:
            sub.add_argument("--source", default=str(ROOT), help="已审查的干净本地 Git 副本")
            sub.add_argument("--revision", required=True, help="固定的已审查 commit")
            sub.add_argument("--legacy", help="明确批准迁移的 V2 本机目录")
        if action == "rollback":
            sub.add_argument("--to", required=True, help="已保留于本机的发行 commit")
            sub.add_argument("--restore-uninstalled", action="store_true")
        if action in {"register", "unregister"}:
            sub.add_argument("--path", required=True)
        if action == "migrate":
            sub.add_argument("--legacy", required=True)
        if action in {"doctor", "status"}:
            sub.add_argument("--cwd")
        if action not in {"doctor", "status", "list"}:
            mode = sub.add_mutually_exclusive_group()
            mode.add_argument("--dry-run", action="store_true")
            mode.add_argument("--apply", action="store_true")
    return cli


def perform(local, args):
    if args.command == "recover":
        return recover(local, args.apply)
    if journal_changes(local)[0] is not None:
        raise ValueError("发现未完成事务，请先运行 recover --dry-run")
    if args.command in {"register", "unregister", "migrate"}:
        plan = project_plan(local, args)
    else:
        plan = lifecycle(local, args)
    if args.apply:
        apply_plan(plan)
    return plan


def main():
    args = parser().parse_args()
    try:
        local = Local(args.home)
        if args.command == "list":
            result = {"version": MANIFEST["version"], "platforms": detected(local)}
        elif args.command in {"status", "doctor"}:
            result = status(local)
            if args.command == "doctor":
                result["environment"] = environment(local)
            if args.cwd:
                result["project"] = detect(args.cwd, local)
        else:
            if args.apply:
                # 先计算一次无副作用计划；存在冲突时不创建锁或目录。
                requested = args.apply
                args.apply = False
                plan = perform(local, args)
                args.apply = requested
                if not plan.conflicts and (plan.changes or args.command == "recover" and journal_changes(local)[0]):
                    with user_lock(local):
                        plan = perform(local, args)
            else:
                plan = perform(local, args)
            result = plan.summary(args.apply and not plan.conflicts and bool(plan.changes))
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 1 if result.get("conflicts") else 0
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        message = str(exc) if not isinstance(exc, subprocess.SubprocessError) else "Git 查询失败或超时"
        print(json.dumps({"error": message, "applied": False}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
