"""构建原生 .skill 文件、比对证据并预演绑定，不连接 Multica 服务。"""
import sys

if __name__ == "__main__":
    sys.dont_write_bytecode = True

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile, ZipInfo

from git_access import SOURCE_URL
from local_state import NAME, ROOT, read, unsafe_link
from release import allowed, reviewed_source, validate_bundle

FILE_LIMIT = 1 << 20
SUPPORT_LIMIT = 8 << 20
SUPPORT_COUNT = 512
UPLOAD_LIMIT = 16 << 20
SENSITIVE = re.compile(
    r"/Users/[A-Za-z0-9_.-]+/|/home/[A-Za-z0-9_.-]+/|[A-Za-z]:[\\/]Users[\\/]"
    r"|gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?i:\b(?:api[_-]?key|password|token|cookie|client[_-]?secret)\s*[:=]\s*['\"][^'\"]{16,}['\"])"
    r"|https?://(?:localhost|[^/\s]+\.(?:internal|local|corp)|127(?:\.\d{1,3}){3}|10(?:\.\d{1,3}){3}"
    r"|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
)


def supporting_path(name):
    if not isinstance(name, str) or any(char in name for char in "\\:\0"):
        return False
    parts = name.split("/")
    reserved = {"skill.md", "license", "license.md", "license.txt"}
    return (all(part and not part.startswith(".") and part != "__MACOSX"
                and part.rstrip(" .") == part and not PureWindowsPath(part).is_reserved() for part in parts)
            and parts[-1].casefold() not in reserved)


def verify_files(files):
    if "SKILL.md" not in files or len(files) - 1 > SUPPORT_COUNT:
        raise ValueError("导入包缺少入口或附属文件超过平台限制")
    if sum(len(data) for name, data in files.items() if name != "SKILL.md") > SUPPORT_LIMIT:
        raise ValueError("导入包附属文件超过 8 MiB")
    normalized = set()
    for name, data in files.items():
        if (not allowed(name) or name.casefold() in normalized
                or name != "SKILL.md" and not supporting_path(name)):
            raise ValueError(f"不允许的发行路径：{name}")
        normalized.add(name.casefold())
        if len(data) > FILE_LIMIT or b"\0" in data:
            raise ValueError(f"文件超过限制或不是纯文本：{name}")
        if SENSITIVE.search(data.decode("utf-8")):
            raise ValueError(f"文件疑似包含凭证或私有位置：{name}")
    return validate_bundle(files)


def fingerprint(files):
    """按 daemon 回执的文件路径及长度帧计算完整 SHA-256。"""
    digest = hashlib.sha256()
    for name, body in sorted(files.items()):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(len(body).to_bytes(8, "big"))
        digest.update(body)
    return digest.hexdigest()


def summary(files):
    sha = fingerprint(files)
    return {"version": verify_files(files), "sha256": sha, "receipt_prefix": sha[:12],
            "supporting_files": len(files) - 1,
            "supporting_bytes": sum(len(data) for name, data in files.items() if name != "SKILL.md"),
            "primary_bytes": len(files["SKILL.md"]),
            "largest_file_bytes": max(map(len, files.values()))}


def build_archive(files):
    verify_files(files)
    stream = io.BytesIO()
    with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            member = ZipInfo(f"{NAME}/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            member.create_system = 3
            member.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(member, data, compress_type=ZIP_DEFLATED)
    blob = stream.getvalue()
    if len(blob) >= UPLOAD_LIMIT:
        raise ValueError("归档已达到上传上限，需预留 multipart 开销")
    return blob


def read_archive(blob):
    if blob is None or len(blob) >= UPLOAD_LIMIT:
        raise ValueError("归档缺失或超过上传限制")
    files = {}
    total = 0
    prefix = NAME + "/"
    with ZipFile(io.BytesIO(blob)) as archive:
        members = archive.infolist()
        if len(members) > SUPPORT_COUNT + 1:
            raise ValueError("归档文件数超过限制")
        for member in members:
            if not member.filename.startswith(prefix):
                raise ValueError("归档根必须是 Skill 目录")
            name = member.filename[len(prefix):]
            mode = member.external_attr >> 16
            if not allowed(name) or name in files or member.is_dir() or stat.S_ISLNK(mode):
                raise ValueError(f"归档文件路径重复或不安全：{name}")
            total += member.file_size if name != "SKILL.md" else 0
            if member.file_size > FILE_LIMIT or total > SUPPORT_LIMIT:
                raise ValueError("归档解压体积超过限制")
            files[name] = archive.read(member)
    verify_files(files)
    return files


def compare(expected, observed):
    common = expected.keys() & observed.keys()
    missing = sorted(expected.keys() - observed.keys())
    changed = sorted(name for name in common if expected[name] != observed[name])
    extras = sorted(observed.keys() - expected.keys())
    version = None
    if "manifest.json" in observed:
        try:
            value = json.loads(observed["manifest.json"])
            version = value.get("version") if isinstance(value, dict) else None
        except ValueError:
            pass
    if missing or changed:
        state = "different"
    elif extras:
        state = "expected-files-match-with-extras"
    else:
        state = "match"
    return {"state": state, "version": version, "missing": missing, "changed": changed,
            "extras": extras, "sha256": fingerprint(observed)}


def workspace_files(export):
    if (not isinstance(export, dict) or not isinstance(export.get("content"), str)
            or not isinstance(export.get("files"), list) or len(export["files"]) > SUPPORT_COUNT):
        raise ValueError("需要 multica skill get --with-content 的完整内容")
    files = {"SKILL.md": export["content"].encode("utf-8")}
    seen = {"skill.md"}
    for row in export["files"]:
        if not isinstance(row, dict):
            raise ValueError("工作区证据包含无效的附属文件记录")
        name, body = row.get("path"), row.get("content")
        if not supporting_path(name) or name.casefold() in seen or not isinstance(body, str):
            raise ValueError("工作区证据包含不安全或重复的路径，或缺少正文")
        seen.add(name.casefold())
        files[name] = body.encode("utf-8")
    return files


def runtime_files(folder, paths):
    root = Path(folder).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Runtime Skill 路径必须是目录")
    files = {}
    for name in paths:
        item = root / name
        if not item.is_relative_to(root) or item.resolve() != item:
            raise ValueError(f"Runtime 证据路径发生跳转：{name}")
        content = read(item, limit=FILE_LIMIT)
        if content is not None:
            files[name] = content
    return files


def runtime_evidence(folder, archive, workspace=None):
    expected = workspace if workspace is not None else archive
    observed = runtime_files(folder, expected)
    result = compare(expected, observed)
    return {"scope": "workspace-declared-files" if workspace is not None else "archive-declared-files",
            "comparison": result,
            "receipt_prefix": result["sha256"][:12] if workspace is not None and not result["missing"] else None}


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value):
        raise ValueError("需要可识别的 Multica 对象 ID")
    return value


def plan_binding(inventory, export, agent, bindings, expected, archive, *,
                 workspace, remove=False, reviewed_extras=None):
    workspace = identifier(workspace)
    agent = identifier(agent)
    if not isinstance(bindings, list) or inventory is not None and not isinstance(inventory, list):
        raise ValueError("需要成功的 JSON 清单证据")
    for row in [*(inventory or []), *bindings, *([export] if export is not None else [])]:
        if not isinstance(row, dict) or row.get("workspace_id", workspace) != workspace:
            raise ValueError("快照与指定的工作区不一致")
    command_prefix = ["multica", "--workspace-id", workspace]
    result = {"execute": False, "workspace": workspace, "agent": agent,
              "preserve_bindings": sorted({identifier(row["id"]) for row in bindings})}
    if inventory is None:
        return dict(result, state="inventory-unavailable")
    matches = [row for row in inventory if row["name"].casefold() == NAME]
    if len(matches) > 1:
        return dict(result, state="ambiguous")
    if not matches:
        if remove:
            return dict(result, state="not-bound")
        return dict(result, state="import", command=[*command_prefix, "skill", "import", "--file", archive,
                                                    "--on-conflict", "fail", "--output", "json"])
    skill = identifier(matches[0]["id"])
    assigned = next((row for row in bindings if row["id"] == skill), None)
    result["skill_id"] = skill
    result["preserve_bindings"] = [entry for entry in result["preserve_bindings"] if entry != skill]
    if export is None or export.get("id") != skill or export.get("name") != NAME:
        return dict(result, state="inspect-existing")
    check = compare(expected, workspace_files(export))
    result["comparison"] = check
    if check["state"] == "different":
        return dict(result, state="revision-different")
    if check["state"] == "expected-files-match-with-extras" and check["sha256"] != reviewed_extras:
        return dict(result, state="review-url-extras")
    if remove:
        return dict(result, state="remove-one-in-ui" if assigned else "not-bound")
    if assigned is not None:
        return dict(result, state="enable-in-ui" if assigned.get("enabled") is False else "already-bound")
    return dict(result, state="add", command=[*command_prefix, "agent", "skills", "add", agent,
                                             "--skill-ids", skill, "--output", "json"])


def load_json(path):
    raw = read(Path(path), limit=UPLOAD_LIMIT)
    if raw is None:
        raise ValueError("指定的证据文件不存在")
    return json.loads(raw)


def safe_output(output):
    requested = Path(output).expanduser().absolute()
    parent = requested.parent.resolve(strict=True)
    if (requested.parent != parent or requested.suffix != ".skill"
            or any(os.path.lexists(folder / ".git") for folder in (parent, *parent.parents))
            or os.path.lexists(requested)):
        raise ValueError("归档必须新建为工作树之外的 .skill 普通文件，路径不能经过链接")
    if unsafe_link(parent.lstat()):
        raise ValueError("归档父目录不能为重解析点")
    return requested


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    package = commands.add_parser("package", help="默认预演；--apply 仅生成本地归档")
    package.add_argument("--source", default=str(ROOT))
    package.add_argument("--revision", required=True)
    package.add_argument("--output", required=True)
    modes = package.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--apply", action="store_true")
    verify = commands.add_parser("verify", help="比较本地保存的导入和 Runtime 证据")
    verify.add_argument("--archive", required=True)
    verify.add_argument("--workspace-export")
    verify.add_argument("--runtime-directory")
    verify.add_argument("--runtime-local-directory")
    plan = commands.add_parser("plan", help="根据只读快照生成方案，不运行其中的命令")
    plan.add_argument("--archive", required=True)
    plan.add_argument("--agent", required=True)
    plan.add_argument("--workspace", required=True)
    plan.add_argument("--bindings", required=True)
    plan.add_argument("--inventory")
    plan.add_argument("--workspace-export")
    plan.add_argument("--remove", action="store_true")
    plan.add_argument("--reviewed-extras-sha256", help="已人工审查的完整 URL 导入内容哈希")
    args = parser.parse_args()
    try:
        if args.action == "package":
            target = safe_output(args.output)
            _, files = reviewed_source(args.source, args.revision)
            archive = build_archive(files)
            if args.apply:
                flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
                with os.fdopen(os.open(target, flags, 0o600), "wb") as stream:
                    stream.write(archive)
            result = {**summary(files), "commit": args.revision, "output": str(target),
                      "github_url": f"{SOURCE_URL}/tree/{args.revision}",
                      "archive_bytes": len(archive), "written": args.apply}
        else:
            files = read_archive(read(Path(args.archive), limit=UPLOAD_LIMIT))
            exported = load_json(args.workspace_export) if args.workspace_export else None
            if args.action == "plan":
                inventory = load_json(args.inventory) if args.inventory else None
                result = plan_binding(inventory, exported, args.agent,
                                      load_json(args.bindings), files, args.archive, workspace=args.workspace,
                                      remove=args.remove, reviewed_extras=args.reviewed_extras_sha256)
            else:
                result = {"expected": summary(files)}
                workspace = workspace_files(exported) if args.workspace_export else None
                if workspace is not None:
                    result["workspace"] = compare(files, workspace)
                for field in ("runtime_directory", "runtime_local_directory"):
                    folder = getattr(args, field)
                    if folder:
                        result[field] = runtime_evidence(
                            folder, files, workspace if field == "runtime_directory" else None
                        )
                result["evidence_boundary"] = "文件比对与绑定快照不证明模型已经读取或遵循规则"
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError, BadZipFile) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
