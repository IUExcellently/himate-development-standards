"""用户级路径、文件安全和跨平台锁。"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import uuid
import sys

NAME = "himate-development-standards"
ROOT = Path(__file__).resolve().parents[1]
MAX_FILE = 4 * 1024 * 1024


def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def unsafe_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def inside(path, home):
    """拒绝链接、junction、目录逃逸和已有 Git 工作区。"""
    if not path.is_absolute() or home not in path.parents or ".." in path.parts:
        raise ValueError(f"路径不在用户目录内：{path}")
    relative = path.relative_to(home)
    if any(part.endswith((".", " ")) or ":" in part or Path(part).is_reserved() for part in relative.parts):
        raise ValueError(f"路径包含保留文件名：{path}")
    for item in (home / Path(*relative.parts[:i]) for i in range(1, len(relative.parts) + 1)):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if unsafe_link(info):
            raise ValueError(f"路径包含链接或重解析点：{item}")
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"父路径不是目录：{item}")
        if stat.S_ISDIR(info.st_mode) and os.path.lexists(item / ".git"):
            raise ValueError(f"拒绝写入 Git 工作区：{item}")
    if path.resolve() != path:
        raise ValueError(f"路径解析后发生变化：{path}")


def regular_fd(path, flags, *, parent=None, create_mode=0o600):
    """校验打开后的真实文件与观察的入口一致。"""
    leaf = path if parent is None else path.name

    def info():
        return os.lstat(leaf, dir_fd=parent)

    def check(value):
        if unsafe_link(value) or not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
            raise ValueError(f"需要单链接普通文件：{path}")

    try:
        before = info()
    except FileNotFoundError:
        before = None
    if before is not None:
        check(before)
    options = flags | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(leaf, options, create_mode, dir_fd=parent)
    try:
        actual = os.fstat(fd)
        check(actual)
        after = info()
        check(after)
        if not os.path.samestat(after, actual) or before is not None and not os.path.samestat(before, actual):
            raise ValueError(f"打开期间文件入口发生变化：{path}")
        return fd
    except BaseException:
        os.close(fd)
        raise


def read(path, limit=MAX_FILE, *, parent=None):
    try:
        fd = regular_fd(path, os.O_RDONLY, parent=parent)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as stream:
        if os.fstat(stream.fileno()).st_size > limit:
            raise ValueError(f"文件超过大小限制：{path}")
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise ValueError(f"文件读取超过大小限制：{path}")
    return value


def read_json(path, default=None):
    raw = read(path)
    if raw is None:
        return default
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"预期 JSON 对象：{path}")
    return value


class Local:
    def __init__(self, home=None):
        self.home = Path(home or Path.home()).expanduser().resolve(strict=True)
        if not self.home.is_dir():
            raise ValueError("用户目录必须已存在")
        if any(os.path.lexists(parent / ".git") for parent in (self.home, *self.home.parents)):
            raise ValueError("用户目录不能是 Git 工作树")
        self.state = self.home / f".{NAME}"
        self.registry = self.state / "projects.json"
        self.receipt = self.state / "receipt.json"
        self.journal = self.state / "pending.json"
        inside(self.state, self.home)

    def registrations(self):
        inside(self.registry, self.home)
        value = read_json(self.registry, {"schema_version": 1, "roots": []})
        roots = value.get("roots")
        if value.get("schema_version") != 1 or not isinstance(roots, list) or not all(
            isinstance(p, str) and Path(p).is_absolute() and ".." not in Path(p).parts for p in roots
        ):
            raise ValueError("工作树登记格式无效")
        return value


@contextmanager
def parent_handle(path, home, create=False):
    inside(path, home)
    if os.name == "nt":
        if create:
            path.parent.mkdir(parents=True, exist_ok=True)
        inside(path, home)
        yield None
        return
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(home, flags)
    try:
        for part in path.parent.relative_to(home).parts:
            try:
                child = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def publish_new(source, target, parent):
    """用系统提供的原子无覆盖重命名提交新文件。"""
    if os.name == "nt":
        os.rename(source, target)
        return
    import ctypes

    libc = ctypes.CDLL(None, use_errno=True)
    src, dst = os.fsencode(source.name), os.fsencode(target.name)
    if sys.platform == "darwin" and hasattr(libc, "renameatx_np"):
        rename = libc.renameatx_np
        flag = 0x00000004  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        flag = 1  # RENAME_NOREPLACE
    else:
        raise OSError("当前系统不支持原子无覆盖重命名")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    if rename(parent, src, parent, dst, flag) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def write_file(path, previous, desired, mode=None, *, home):
    """使用同目录暂存文件，POSIX 写入经已打开的父目录描述符。"""
    if previous is None and desired is None:
        return
    with parent_handle(path, home, create=desired is not None) as parent:
        if read(path, parent=parent) != previous:
            raise ValueError(f"写入前文件已变化：{path}")
        leaf = path if parent is None else path.name
        if desired is None:
            os.unlink(leaf, dir_fd=parent)
            return
        effective = mode if mode is not None else (
            stat.S_IMODE(os.lstat(leaf, dir_fd=parent).st_mode) if previous is not None else 0o600
        )
        if parent is None:
            fd, filename = tempfile.mkstemp(prefix=".himate-stage-", dir=path.parent)
            temporary = Path(filename)
            source = temporary
        else:
            temporary = path.with_name(f".himate-stage-{uuid.uuid4().hex}")
            source = temporary.name
            fd = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                if parent is not None:
                    os.fchmod(stream.fileno(), effective)
                stream.write(desired)
                stream.flush()
                os.fsync(stream.fileno())
            if parent is None:
                inside(path, home)
            if previous is None:
                publish_new(temporary, path, parent)
            elif read(path, parent=parent) == previous:
                os.replace(source, leaf, src_dir_fd=parent, dst_dir_fd=parent)
            else:
                raise ValueError(f"替换前文件已变化：{path}")
        finally:
            try:
                os.unlink(source, dir_fd=parent)
            except FileNotFoundError:
                pass


@contextmanager
def user_lock(local):
    lock = local.state / "lock"
    with parent_handle(lock, local.home, create=True) as parent:
        fd = regular_fd(lock, os.O_RDWR | os.O_CREAT, parent=parent)
        with os.fdopen(fd, "r+b") as handle:
            if os.name == "nt":
                import msvcrt
                if not handle.read(1):
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
