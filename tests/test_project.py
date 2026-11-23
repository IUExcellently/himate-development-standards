import json
from pathlib import Path
import tempfile
import unittest

from support import git, project
from detect_project import detect
from local_state import Local
from resolve_rules import resolve
from snapshot import capture


class ProjectTest(unittest.TestCase):
    def setUp(self):
        self.direct = tempfile.TemporaryDirectory(prefix="HiMate 项目 ")
        self.addCleanup(self.direct.cleanup)
        temp = Path(self.direct.name)
        home = temp / "home"
        home.mkdir()
        self.local = Local(home)
        self.repo = project(temp / "已登记 项目")

    def register(self, *paths):
        self.local.state.mkdir(exist_ok=True)
        data = {"schema_version": 1, "roots": [str(path.resolve()) for path in paths]}
        self.local.registry.write_text(json.dumps(data), encoding="utf-8")

    def test_registration_worktrees_and_no_writes(self):
        worktree = self.repo.parent / "分离 工作树"
        git(self.repo, "worktree", "add", "-q", "--detach", str(worktree))
        self.assertFalse(detect(self.repo, self.local)["active"])
        self.register(self.repo, worktree)
        before = capture(self.repo)
        self.assertTrue(detect(self.repo / "backend", self.local)["active"])
        self.assertTrue(detect(worktree, self.local)["active"])
        self.assertFalse(detect(self.repo / "missing", self.local)["active"])
        self.assertEqual(before, capture(self.repo))

    def test_nonmatching_and_nested_worktree(self):
        fake = project(self.repo.parent / "himate", signatures=False)
        copy = project(self.repo.parent / "其他")
        nested = project(self.repo / "嵌套")
        self.register(self.repo, fake)
        self.assertFalse(detect(fake, self.local)["active"])
        self.assertFalse(detect(copy, self.local)["active"])
        self.assertEqual(detect(nested, self.local)["reason"], "different-git-root")
        self.register(nested, self.repo)
        self.assertTrue(detect(nested, self.local)["active"])

    def test_registered_symlink(self):
        self.register(self.repo)
        link = self.repo.parent / "入口"
        try:
            link.symlink_to(self.repo, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"当前文件系统不允许创建测试符号链接：{exc}")
        self.assertTrue(detect(link, self.local)["active"])

    def test_router_specialties_and_incremental_loading(self):
        self.register(self.repo)
        samples = [
            ("", "frontend/apps/admin/a.less", "frontend-styles"),
            ("", "backend/controller/TestController.java", "03-api-design"),
            ("更新状态", "backend/service/AccountService.java", "04-transaction"),
            ("", "backend/sql/migration/Init.sql", "05-sql-guidelines"),
            ("调整HikariCP和Kafka配置", "backend/application.yml", "07-connection-pool"),
            ("优化Kafka消费者", "backend/Application.java", "09-cache-messaging"),
            ("LangGraph Redis", "himate-dispatcher/app/agents/model.py", "python-dispatcher"),
            ("调整AG-UI事件", "docs/contracts/agui-v1/README.md", "api-contracts"),
        ]
        for task, path, rule in samples:
            with self.subTest(rule=rule):
                answer = resolve(self.repo, task, [path], local=self.local)
                self.assertIn(f"{rule}.md", {Path(name).name for name in answer["rules"]})
                if path.startswith("himate-dispatcher"):
                    self.assertFalse(any("/backend/" in name for name in answer["rules"]))
        paths = ["frontend/apps/admin/a.css", "backend/ItemController.java",
                 "himate-dispatcher/app/api/dispatch.py", "frontend/apps/admin/a.css"]
        before = resolve(self.repo, "AG-UI", paths, local=self.local)
        after = resolve(self.repo, "AG-UI", paths, loaded=before["rules"], local=self.local)
        self.assertEqual(after["rules"], [])
        self.assertEqual(after["already_loaded"], before["rules"])
        self.assertEqual(len(set(before["rules"])), len(before["rules"]))
        escaped = resolve(self.repo, paths=["../../backend/Unsafe.java"], local=self.local)
        self.assertEqual(escaped["unrouted"], ["../../backend/Unsafe.java"])

    def test_cli_routing_with_non_unicode_terminal_encoding(self):
        import os
        import subprocess
        import sys
        from support import ROOT

        self.register(self.repo)
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "resolve_rules.py"), "--home", str(self.local.home),
             "--cwd", str(self.repo), "--path", "未知/前端.ts"],
            env=dict(os.environ, PYTHONIOENCODING="cp1252"),
            capture_output=True, check=True, encoding="ascii", timeout=10,
        )
        self.assertTrue(json.loads(result.stdout)["active"])
        self.assertEqual(json.loads(result.stdout)["unrouted"], ["未知/前端.ts"])
