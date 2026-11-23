"""从工作路径、文件、任务语义选规则，只输出建议。"""
import argparse
import json
from pathlib import Path
import re
import sys

if __name__ == "__main__":
    sys.dont_write_bytecode = True

from detect_project import MANIFEST, detect
from local_state import Local

TOPIC_PATTERNS = {
    "frontend": r"前端|移动端|管理端|\b(?:frontend|react|vite|zustand|semi|vitest)\b",
    "styles": r"样式|覆盖.*弹窗|\b(?:css|less|tailwind)\b",
    "java": r"后端|\b(?:java|maven|spring(?:[ -]boot)?)\b",
    "controller": r"控制器|\bcontroller\b",
    "service": r"服务层|\bservice layer\b",
    "sql": r"慢查询|执行计划|索引|\b(?:sql|mapper|mybatis|explain|jdbc)\b",
    "schema": r"数据库|迁移脚本|回填|\b(?:postgresql|ddl|migration)\b",
    "pool": r"连接池|读写分离|\b(?:hikaricp|hikari|datasource|connection pool)\b",
    "transaction": r"事务|回滚|死锁|\b(?:transaction|transactional|rollback)\b",
    "concurrency": r"并发写|并发控制|线程池|虚拟线程|\b(?:executor|virtual threads?|completablefuture|async java)\b",
    "middleware": r"缓存一致性|定时任务|死信|\b(?:redis|kafka|xxl.job|redisson|dlq)\b",
    "security": r"鉴权|越权|后端权限|\b(?:authorization|spring security)\b",
    "observability": r"可观测|链路追踪|后端日志|\b(?:micrometer|actuator|mdc)\b",
    "java_test": r"后端测试|\b(?:junit|mockito|p3c|spotbugs|checkstyle|pmd)\b",
    "dispatcher": r"调度器|\b(?:python|dispatcher|fastapi|langgraph|deepagents|ruff)\b",
    "contract": r"跨端|契约|状态码|流式事件|接口(?:新增|变更|字段|兼容)|\b(?:api contract|sse|ag.ui|ui.block|openapi)\b",
    "dependencies": r"依赖|锁文件|\b(?:dependency|dependencies|lockfile|requirements)\b",
}

JAVA_ONLY = {"java", "controller", "service", "sql", "schema", "pool", "transaction",
             "concurrency", "middleware", "security", "observability", "java_test"}


def path_tags(path):
    value = path.as_posix().lower()
    name = path.name.lower()
    tags = set()
    if value.startswith("frontend/"):
        tags.add("frontend")
        if path.suffix.lower() in {".css", ".less", ".scss"}:
            tags.add("styles")
        if any(part in value for part in ("chat-transport", "platform-contract", "ui-protocol", "ui-block")):
            tags.add("contract")
    elif value.startswith("himate-dispatcher/"):
        tags.add("dispatcher")
        if "/api/" in value or "/schemas/" in value or "/clients/adapter" in value:
            tags.add("contract")
    elif value.startswith("docs/contracts/"):
        tags.add("contract")
    elif value.startswith("backend/"):
        tags.add("java")
        if path.suffix.lower() == ".sql":
            tags.add("sql")
            if "/migration/" in value or "baseline" in name or name.startswith("init-"):
                tags.add("schema")
        if re.search(r"(?:/mapper/|mapper\.(?:java|xml)$)", value):
            tags.add("sql")
        if re.search(r"/(?:controller|dto|feign|vo)/|controller\.java$", value):
            tags.add("controller")
        if "/service/" in value or re.search(r"service(?:impl)?\.java$", name):
            tags.add("service")
        if "/test/" in value or name.endswith("test.java"):
            tags.add("java_test")
        if re.search(r"hikari|datasource|connectionpool", value):
            tags.add("pool")
        if re.search(r"transaction", name):
            tags.add("transaction")
        if re.search(r"executor|threadpool|asyncconfig", name):
            tags.add("concurrency")
        if re.search(r"redis|kafka|xxl.?job|/job/|consumer\.java$", value):
            tags.add("middleware")
        if re.search(r"security|authfilter", name):
            tags.add("security")
        if re.search(r"logback|mdcscope|metric", name):
            tags.add("observability")
        if re.search(r"/sse/|dispatcher-protocol|ui.?block|/agui/", value):
            tags.add("contract")
    if name in {"package.json", "pnpm-workspace.yaml", "pnpm-lock.yaml", "pom.xml",
                "pyproject.toml", "uv.lock"} or re.fullmatch(r"requirements.*\.txt", name):
        tags.add("dependencies")
    return tags


def resolve(cwd, task="", paths=(), explicit=(), loaded=(), local=None):
    project = detect(cwd, local)
    if not project["active"]:
        return {**project, "tags": [], "rules": [], "already_loaded": [], "unrouted": []}
    repo = Path(project["root"])
    here = Path(cwd).expanduser().resolve()
    tags = set(explicit)
    inferred = set()
    unrouted = []
    for item in paths:
        path = Path(item).expanduser()
        root_candidate = repo / path
        try:
            if path.is_absolute():
                target = path.resolve()
            elif path.parts and path.parts[0] in {"frontend", "backend", "himate-dispatcher", "docs"}:
                target = root_candidate.resolve()
            else:
                target = (here / path).resolve()
        except (OSError, RuntimeError, ValueError):
            unrouted.append(item)
            continue
        if repo not in target.parents:
            unrouted.append(item)
            continue
        candidates = path_tags(target.relative_to(repo))
        if not candidates:
            unrouted.append(item)
        inferred.update(candidates)
    semantic = {tag for tag, pattern in TOPIC_PATTERNS.items() if re.search(pattern, task, re.I | re.ASCII)}
    if "java" not in inferred | tags | semantic and {"frontend", "dispatcher"} & (inferred | tags | semantic):
        # Python 的 Redis 和前端的 API 文案不自动引入 Java 规则。
        semantic.difference_update(JAVA_ONLY)
    tags.update(inferred | semantic)
    if "java" in inferred | tags and "service" in tags and re.search(r"写入|更新|删除|批量|幂等|\bwrite\b", task, re.I | re.ASCII):
        tags.add("transaction")
    if any(tag in JAVA_ONLY for tag in tags) and re.search(r"审查|复核|验收|\breview\b", task, re.I | re.ASCII):
        tags.add("java_test")
    rules = dict.fromkeys(MANIFEST["base"])
    if any(set(MANIFEST["tags"][tag]) & set(MANIFEST["backend"]) for tag in tags):
        rules.update(dict.fromkeys(MANIFEST["tags"]["java"]))
    for tag in MANIFEST["tags"]:
        if tag in tags:
            rules.update(dict.fromkeys(MANIFEST["tags"][tag]))
    loaded = set(loaded)
    return {**project, "tags": sorted(tags), "rules": [p for p in rules if p not in loaded],
            "already_loaded": [p for p in rules if p in loaded], "unrouted": unrouted}


def route_arguments(parser):
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--home", help="独立的测试用户目录")
    parser.add_argument("--task", default="")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--tag", action="append", choices=sorted(MANIFEST["tags"]), default=[])
    parser.add_argument("--loaded", action="append", default=[])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    route_arguments(parser)
    args = parser.parse_args()
    print(json.dumps(resolve(args.cwd, args.task, args.path, args.tag, args.loaded, Local(args.home)),
                     ensure_ascii=True, indent=2))
