"""从经审查的固定 Git 提交提取使用文件，不运行候选版本代码。"""
import json
from pathlib import Path, PurePosixPath
import stat
import re
import sys

from git_access import SOURCE_URL, git, git_root
from local_state import NAME, digest, encode, inside, read, read_json, unsafe_link

SHA = re.compile(r"[0-9a-f]{40}")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){2}")
FRONTMATTER = re.compile(r"^---\nname: " + NAME + r"\ndescription: ([^\n]{1,1024})\n---\n")
LIMIT = 1024 * 1024
TEMPLATE = "integrations/SKILL.template.md"
RUNTIME = {"cli", "local_state", "git_access", "detect_project", "resolve_rules",
           "release", "transactions", "integrations", "resolve_conflict", "legacy"}


def allowed(relative):
    if relative in {"SKILL.md", "manifest.json", "integrations/SKILL.template.md"}:
        return True
    p = PurePosixPath(relative)
    return p.as_posix() == relative and not p.is_absolute() and all(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", part) for part in p.parts
    ) and (p.parts[0] in {"standards", "references"} and p.suffix == ".md"
           or len(p.parts) == 2 and p.parts[0] == "scripts" and p.suffix == ".py" and p.stem in RUNTIME)


def validate_bundle(files):
    manifest = json.loads(files["manifest.json"])
    version = manifest.get("version")
    requires = manifest.get("requires_python")
    if manifest.get("schema_version") != 3 or not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("候选版本格式或 schema 不兼容")
    if not isinstance(requires, list) or len(requires) != 2 or not all(type(n) is int and n >= 0 for n in requires):
        raise ValueError("候选 Python 版本要求无效")
    if tuple(sys.version_info[:2]) < tuple(requires):
        raise ValueError("当前 Python 版本不满足候选版本要求")
    if "root" in manifest or "roots" in manifest["project"]:
        raise ValueError("公开清单包含本机注册项")
    if not FRONTMATTER.match(files["SKILL.md"].decode("utf-8")):
        raise ValueError("Skill 元数据无效")
    template = files[TEMPLATE].decode("utf-8")
    if not FRONTMATTER.match(template) or sorted(re.findall(r"@@([A-Z_]+)@@", template)) != ["BODY", "DETECT"]:
        raise ValueError("发行入口模板元数据或占位符无效")
    rules = set(manifest["base"]) | set(manifest["backend"])
    rules.update(path for group in manifest["tags"].values() for path in group)
    minimum = rules | {"integrations/SKILL.template.md"} | {f"scripts/{name}.py" for name in RUNTIME}
    if len(set(manifest["backend"])) != 12 or not minimum <= files.keys():
        raise ValueError("规则或运行文件不完整")
    if any(not path.startswith("standards/") or not path.endswith(".md") for path in rules):
        raise ValueError("规则索引路径无效")
    return version


def reviewed_source(source, revision):
    if not revision or not SHA.fullmatch(revision):
        raise ValueError("需要已审查的 40 位小写 Git commit（--revision）")
    source = Path(source).expanduser().resolve(strict=True)
    if git_root(source) != source:
        raise ValueError("候选路径必须是独立仓库根")
    origin = git(source, "config", "--local", "--get-all", "remote.origin.url").decode().splitlines()
    if origin not in ([SOURCE_URL], [SOURCE_URL + ".git"]):
        raise ValueError("候选仓库 origin 不匹配")
    if git(source, "rev-parse", "HEAD").decode().strip() != revision:
        raise ValueError("候选 HEAD 与固定版本不一致")
    tree = {}
    total = 0
    for row in git(source, "ls-tree", "-rlz", "--full-tree", revision).split(b"\0"):
        if not row:
            continue
        meta, name = row.split(b"\t", 1)
        mode, kind, oid, size = meta.decode("ascii").split()
        relative = name.decode("utf-8")
        path = PurePosixPath(relative)
        if any(
            not re.fullmatch(r"[A-Za-z0-9._-]+", part) or part in {".", ".."} or part.endswith(".")
            for part in path.parts
        ) or path.is_absolute() or path.as_posix() != relative:
            raise ValueError(f"候选包含不可携带路径：{relative}")
        if mode not in {"100644", "100755"} or kind != "blob" or not SHA.fullmatch(oid):
            raise ValueError(f"候选包含链接或非普通文件：{relative}")
        total += int(size)
        if total > 4 * LIMIT:
            raise ValueError("候选审查内容超过大小限制")
        tree[relative] = (mode, oid, int(size))
    index = {}
    for row in git(source, "ls-files", "--stage", "-z").split(b"\0"):
        if not row:
            continue
        meta, name = row.split(b"\t", 1)
        mode, oid, stage = meta.decode("ascii").split()
        if stage != "0":
            raise ValueError("候选工作树有未解决冲突")
        index[name.decode("utf-8")] = (mode, oid)
    if index != {name: info[:2] for name, info in tree.items()} or git(
        source, "ls-files", "-z", "--others", "--exclude-standard"
    ):
        raise ValueError("候选工作树有未提交修改")
    # 直接比较索引和 Git blob，避免 git status 触发候选仓库的 clean filter。
    names = list(tree)
    query = "".join(f"{tree[name][1]}\n" for name in names).encode("ascii")
    contents = git(source, "cat-file", "--batch", input=query)
    offset = 0
    files = {}
    runtime_size = 0
    for name in names:
        _, oid, size = tree[name]
        header = f"{oid} blob {size}\n".encode("ascii")
        if not contents.startswith(header, offset):
            raise ValueError("候选对象类型或长度与 Git 树不符")
        start = offset + len(header)
        data = contents[start:start + size]
        offset = start + size + 1
        if contents[offset - 1:offset] != b"\n":
            raise ValueError("候选对象长度无效")
        local_file = source / name
        if local_file.resolve() != local_file:
            raise ValueError(f"候选工作树路径发生跳转：{name}")
        checked = read(local_file, limit=4 * LIMIT)
        if checked != data and (checked is None or b"\0" in data or checked.replace(b"\r\n", b"\n") != data):
            raise ValueError(f"候选工作树有未提交修改：{name}")
        if allowed(name):
            runtime_size += size
            if runtime_size > LIMIT:
                raise ValueError("候选运行文件超过大小限制")
            data.decode("utf-8")
            files[name] = data.replace(b"\r\n", b"\n")
        elif name.startswith(("standards/", "references/")):
            raise ValueError("候选规范包含非发行文件")
    return validate_bundle(files), files


def bundle_path(local, revision):
    if not isinstance(revision, str) or not SHA.fullmatch(revision):
        raise ValueError("发行版本标识无效")
    return local.state / "releases" / revision / NAME


def verify_layout(root, files):
    """拒绝索引外内容，尤其是可能遮蔽运行模块的附加文件。"""
    parents = {p for name in files for p in PurePosixPath(name).parents if p != PurePosixPath(".")}
    stack = [root] if root.is_dir() else []
    while stack:
        for path in stack.pop().iterdir():
            rel = PurePosixPath(path.relative_to(root).as_posix())
            info = path.lstat()
            if not unsafe_link(info):
                if stat.S_ISDIR(info.st_mode) and rel in parents:
                    stack.append(path)
                    continue
                if stat.S_ISREG(info.st_mode) and rel.as_posix() in files:
                    continue
            raise ValueError(f"发行目录包含额外或不安全的内容：{path}")


def release_changes(local, revision, files, add):
    target = bundle_path(local, revision)
    inside(target / "bundle.json", local.home)
    verify_layout(target, set(files) | {"bundle.json"})
    index = {"files": {name: digest(data) for name, data in files.items()}}
    for name, data in {**files, "bundle.json": encode(index)}.items():
        path = target / name
        inside(path, local.home)
        before = read(path)
        if before is not None and before != data:
            raise ValueError(f"已有发行缓存内容不符：{path}")
        add(path, before, data)
    return target


def recorded_release(local, revision):
    target = bundle_path(local, revision)
    inside(target / "bundle.json", local.home)
    index = read_json(target / "bundle.json")
    if index is None:
        raise ValueError("本地没有已记录的该版本")
    verify_layout(target, set(index["files"]) | {"bundle.json"})
    files = {}
    for name, expected in index["files"].items():
        if not allowed(name):
            raise ValueError("发行记录路径无效")
        path = target / name
        inside(path, local.home)
        data = read(path)
        if data is None or digest(data) != expected:
            raise ValueError(f"已安装发行文件缺失或被修改：{path}")
        files[name] = data
    return validate_bundle(files), files
