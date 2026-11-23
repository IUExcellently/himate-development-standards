"""只读 Git 查询，避免继承调用者的仓库重定向。"""
import os
from pathlib import Path
import subprocess

SOURCE_URL = "https://github.com/IUExcellently/himate-development-standards"


def git(cwd, *args, input=None):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0",
               GIT_NO_REPLACE_OBJECTS="1", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
         "-C", str(cwd), *args], stderr=subprocess.DEVNULL, env=env, timeout=10, input=input,
    )


def git_root(cwd):
    return Path(os.fsdecode(git(cwd, "rev-parse", "--show-toplevel")).rstrip("\r\n")).resolve(strict=True)
