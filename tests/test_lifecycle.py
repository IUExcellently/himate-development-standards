"""测试在独立合成用户目录中运行。"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InitialContract(unittest.TestCase):
    def test_doctor_read_only_without_state(self):
        with tempfile.TemporaryDirectory(prefix="HiMate 测试 ") as folder:
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/cli.py"), "doctor", "--home", folder],
                capture_output=True, encoding="utf-8", check=True,
            )
            self.assertEqual(json.loads(result.stdout)["version"], "3.0.0")
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_public_project_template_contains_no_registrations(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("root", manifest)
        self.assertNotIn("roots", manifest["project"])


from unittest import mock

from support import bump, git, project, source
from integrations import PLATFORMS, entry
from local_state import Local, digest, encode
from transactions import Plan, apply_plan, recover, replace_change, save_journal


class LifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix="HiMate 发行 ")
        cls.addClassCleanup(cls.shared.cleanup)
        folder = Path(cls.shared.name)
        cls.source = folder / "repo"
        cls.first = source(cls.source)
        template = cls.source / "integrations" / "SKILL.template.md"
        with template.open("a", encoding="utf-8") as stream:
            stream.write("\n用于验证升级模板。\n")
        cls.second = bump(cls.source, "3.0.1")
        cls.version1 = folder / "old"
        git(folder, "clone", "-q", str(cls.source), str(cls.version1))
        upstream = git(cls.source, "remote", "get-url", "origin")
        git(cls.version1, "remote", "set-url", "origin", upstream)
        git(cls.version1, "checkout", "-q", "--detach", cls.first)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="HiMate 用户 ")
        self.addCleanup(self.temp.cleanup)
        self.local = Local(self.temp.name)

    def cli(self, action, *args, expected=0, env=None):
        run = subprocess.run(
            [sys.executable, str(ROOT / "scripts/cli.py"), action, "--home", self.temp.name, *map(str, args)],
            capture_output=True, encoding="utf-8", env=env, timeout=25,
        )
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
        return json.loads(run.stdout or run.stderr)

    def install(self, *args, expected=0):
        return self.cli("install", "--source", self.version1, "--revision", self.first,
                        *args, expected=expected)

    def test_install_idempotence_and_uninstall_partial(self):
        agent_file = self.local.home / ".codex" / "AGENTS.md"
        agent_file.parent.mkdir()
        agent_file.write_bytes(b"user\r\n")
        other = self.local.home / ".agents" / "skills" / "another" / "SKILL.md"
        other.parent.mkdir(parents=True)
        other.write_bytes(b"other")
        flags = [value for name in PLATFORMS for value in ("--platform", name)]
        result = self.install(*flags, "--dry-run")
        self.assertTrue(result["requires_apply"])
        self.assertFalse(self.local.state.exists())
        self.install(*flags, "--apply")
        result = self.install(*flags, "--apply")
        self.assertEqual(result["changes"], [])
        self.assertTrue(all(item["matches_receipt"] for item in self.cli("status")["platforms"].values()))
        self.cli("uninstall", "--platform", "kiro", "--apply")
        self.assertFalse(entry(self.local, "kiro").exists())
        self.assertTrue(entry(self.local, "codex").exists())
        entry(self.local, "claude").unlink()
        self.cli("uninstall", "--apply")
        self.assertEqual(self.cli("uninstall", "--dry-run")["changes"], [])
        self.assertEqual(agent_file.read_bytes(), b"user\r\n")
        self.assertEqual(other.read_bytes(), b"other")
        self.cli("rollback", "--to", self.first, "--restore-uninstalled", "--apply")
        self.assertTrue(entry(self.local, "codex").exists())
        self.assertFalse(entry(self.local, "kiro").exists())

    def test_unknown_and_edited_skill_are_preserved(self):
        path = entry(self.local, "codex")
        path.parent.mkdir(parents=True)
        path.write_bytes(b"mine")
        result = self.install("--platform", "codex", "--apply", expected=1)
        self.assertTrue(result["conflicts"])
        self.assertFalse(self.local.state.exists())
        self.assertEqual(path.read_bytes(), b"mine")
        path.unlink()
        self.install("--platform", "codex", "--apply")
        path.write_bytes(b"edited")
        self.assertTrue(self.cli("uninstall", "--apply", expected=1)["conflicts"])
        self.assertEqual(path.read_bytes(), b"edited")

    def test_pinned_update_and_rollback(self):
        self.install("--platform", "qoder", "--apply")
        unchanged = self.cli("update", "--source", self.version1, "--revision", self.first, "--apply")
        self.assertEqual(unchanged["changes"], [])
        path = entry(self.local, "qoder")
        old = path.read_bytes()
        self.cli("update", "--source", self.source, "--revision", self.second, "--dry-run")
        self.assertEqual(path.read_bytes(), old)
        self.cli("update", "--source", self.source, "--revision", self.second, "--apply")
        self.assertEqual(self.cli("status")["installed_version"], "3.0.1")
        self.assertIn("用于验证升级模板。", path.read_text(encoding="utf-8"))
        self.cli("rollback", "--to", self.first, "--apply")
        self.assertEqual(path.read_bytes(), old)

    def test_dirty_missing_and_untrusted_sources(self):
        self.install("--platform", "codex", "--apply")
        fake = self.local.home / "unclean"
        git(self.local.home, "clone", "-q", str(self.source), str(fake))
        origin = git(self.source, "remote", "get-url", "origin")
        git(fake, "remote", "set-url", "origin", origin)
        (fake / "dirty.txt").write_text("edit")
        self.assertIn("未提交", self.cli("update", "--source", fake, "--revision", self.second,
                                         "--apply", expected=1)["error"])
        git(fake, "remote", "set-url", "origin", "https://example.invalid/untrusted")
        self.assertIn("origin", self.cli("update", "--source", fake, "--revision", self.second,
                                        expected=1)["error"])
        self.assertIn("error", self.cli("update", "--source", self.local.home / "下载失败",
                                       "--revision", self.second, expected=1))
        self.assertEqual(self.cli("status")["active_release"], self.first)

    def test_missing_git_and_old_python(self):
        import os
        env = dict(os.environ, PATH="")
        self.assertFalse(self.cli("doctor", env=env)["environment"]["git"])
        self.assertIn("error", self.cli("install", "--platform", "codex", "--source", self.version1,
                                       "--revision", self.first, env=env, expected=1))
        self.assertFalse(self.local.state.exists())
        result = subprocess.run(
            [sys.executable, "-B", "-c", "import runpy, sys; sys.version_info=(3,9); runpy.run_path(sys.argv[1],run_name='__main__')",
             str(ROOT / "scripts/cli.py")], capture_output=True, encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("3.10", result.stderr)

    def test_permission_failure_and_interrupted_recovery(self):
        pending = Plan(self.local)
        skill = entry(self.local, "codex")
        pending.add(skill, None, b"entry")
        pending.add(self.local.receipt, None, b"receipt")

        def denied(local, change, migration, reverse=False):
            if change.path == local.receipt and not reverse:
                raise PermissionError("simulated")
            return replace_change(local, change, migration, reverse)

        with mock.patch("transactions.replace_change", side_effect=denied):
            with self.assertRaises(PermissionError):
                apply_plan(pending)
        self.assertFalse(skill.exists())
        self.assertFalse(self.local.journal.exists())
        save_journal(pending)
        replace_change(self.local, pending.changes[skill], False)
        self.assertTrue(self.cli("recover", "--dry-run")["changes"])
        self.assertTrue(skill.exists())
        self.cli("recover", "--apply")
        self.assertFalse(skill.exists())
        self.assertFalse(self.local.journal.exists())

    def test_legacy_registration_and_installed_entry_migration(self):
        old = self.local.home / "legacy"
        old.mkdir()
        (old / "manifest.json").write_bytes(encode({
            "schema_version": 1, "custom": {"retain": True},
            "project": {"roots": [str(self.local.home / "missing")], "custom": 1},
        }))
        self.cli("migrate", "--legacy", old, "--dry-run")
        self.assertFalse(self.local.state.exists())
        self.cli("migrate", "--legacy", old, "--apply")
        self.assertTrue(self.local.registrations()["legacy"][0]["custom"]["retain"])
        adapter = old / "integrations" / "codex"
        adapter.mkdir(parents=True)
        (old / ".install-state").mkdir()
        skill = entry(self.local, "codex")
        skill.parent.mkdir(parents=True)
        skill.write_bytes(b"legacy skill")
        (adapter / "SKILL.md").write_bytes(skill.read_bytes())
        global_doc = self.local.home / ".codex" / "AGENTS.md"
        global_doc.parent.mkdir()
        fragment = b"<!-- BEGIN HIMATE DEVELOPMENT STANDARDS -->\nlegacy\n<!-- END HIMATE DEVELOPMENT STANDARDS -->\n"
        (adapter / "AGENTS.fragment.md").write_bytes(fragment)
        global_doc.write_bytes(b"original\r\n" + b"\r\n" * 2 + fragment.replace(b"\n", b"\r\n"))
        import base64
        record = {
            str(skill): {"original": None, "installed_sha256": digest(skill.read_bytes())},
            str(global_doc): {"original": base64.b64encode(b"original\r\n").decode(),
                              "installed_sha256": digest(global_doc.read_bytes())},
        }
        (old / ".install-state" / "codex.json").write_bytes(encode({"installed": True, "files": record}))
        self.install("--platform", "codex", "--legacy", old, "--dry-run")
        self.assertEqual(skill.read_bytes(), b"legacy skill")
        self.install("--platform", "codex", "--legacy", old, "--apply")
        self.assertNotEqual(skill.read_bytes(), b"legacy skill")
        self.assertEqual(global_doc.read_bytes(), b"original\r\n")
        self.assertTrue((self.local.state / "legacy-backup.json").exists())
        repeated = self.install("--platform", "codex", "--legacy", old, "--apply")
        self.assertEqual(repeated["changes"], [])

    def test_release_rejects_unmanaged_file(self):
        from release import bundle_path

        first = bundle_path(self.local, self.first)
        extra = first / "scripts" / "unmanaged.py"
        extra.parent.mkdir(parents=True)
        extra.write_bytes(b"# locally added")
        self.assertIn("额外", self.install("--platform", "codex", "--apply", expected=1)["error"])
        extra.unlink()
        self.install("--platform", "codex", "--apply")
        extra.write_bytes(b"# locally added")
        self.assertIn("额外", self.cli("status", expected=1)["error"])
        self.assertIn("额外", self.cli("rollback", "--to", self.first, expected=1)["error"])

    def test_project_home_and_link_destinations_refused(self):
        repo = project(self.local.home / "项目")
        nested_home = repo / "nested"
        nested_home.mkdir()
        with self.assertRaisesRegex(ValueError, "Git"):
            Local(nested_home)
        from snapshot import capture

        before = capture(repo)
        target = self.local.home / ".agents"
        try:
            target.symlink_to(repo, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"当前文件系统不允许创建测试符号链接：{exc}")
        self.assertIn("路径", self.install("--platform", "codex", "--apply", expected=1)["error"])
        self.assertEqual(before, capture(repo))
        self.assertFalse(self.local.state.exists())

    def test_recovery_resumes_legacy_tail(self):
        old = self.local.home / ".codex" / "AGENTS.md"
        old.parent.mkdir()
        original = b"original plus legacy suffix"
        restored = b"original"
        old.write_bytes(original)
        plan = Plan(self.local, migration=True)
        plan.add(old, original, restored)
        save_journal(plan)
        old.write_bytes(b"original plus leg")
        self.cli("recover", "--dry-run")
        self.cli("recover", "--apply")
        self.assertEqual(old.read_bytes(), original)
        self.assertFalse(self.local.journal.exists())

    def test_hard_interrupt_during_publish_can_be_retried_after_recovery(self):
        runner = r"""
import os
import runpy
import sys
from pathlib import Path

launcher, home, source, revision, destination = sys.argv[1:]
sys.path.insert(0, str(Path(launcher).parent))
import local_state

publish = local_state.publish_new

def interrupted(candidate, target, *parents):
    if target.absolute() == Path(destination):
        os._exit(91)
    return publish(candidate, target, *parents)

local_state.publish_new = interrupted
sys.argv = [launcher, "install", "--home", home, "--source", source,
            "--revision", revision, "--platform", "codex", "--apply"]
runpy.run_path(launcher, run_name="__main__")
"""
        from release import bundle_path

        for target in (bundle_path(self.local, self.first) / "SKILL.md", entry(self.local, "codex")):
            with self.subTest(target=target):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", runner, str(ROOT / "scripts" / "cli.py"),
                     str(self.local.home), str(self.version1), self.first, str(target)],
                    capture_output=True, timeout=25,
                )
                self.assertEqual(result.returncode, 91, result.stderr)
                self.assertTrue(self.local.journal.exists())
                self.assertTrue(self.cli("recover", "--apply")["applied"])
                self.install("--platform", "codex", "--apply")
                self.assertTrue(self.cli("status")["platforms"]["codex"]["matches_receipt"])
                self.cli("uninstall", "--apply")

    def test_oversized_migration_state_is_rejected_before_writing(self):
        from local_state import MAX_FILE

        old = self.local.home / "legacy"
        old.mkdir()
        self.local.state.mkdir()
        original = encode({"schema_version": 1, "roots": [], "custom": "a" * (MAX_FILE // 2)})
        self.local.registry.write_bytes(original)
        (old / "manifest.json").write_bytes(encode({
            "schema_version": 1, "project": {"roots": []}, "custom": "b" * (MAX_FILE // 2),
        }))
        result = self.cli("migrate", "--legacy", old, "--dry-run", expected=1)
        self.assertIn("大小限制", result["error"])
        self.assertEqual(self.local.registry.read_bytes(), original)
        self.assertEqual({p.name for p in self.local.state.iterdir()}, {"projects.json"})

    def test_candidate_requires_valid_signature_definitions(self):
        from release import reviewed_source, validate_bundle

        _, bundle = reviewed_source(self.version1, self.first)
        for signatures in (None, {}, {"README.md": []}, {"../README.md": ["HiMate"]},
                           {"C:\\external": ["HiMate"]}, {"README.md": [123]}):
            with self.subTest(signatures=signatures):
                manifest = json.loads(bundle["manifest.json"])
                if signatures is None:
                    del manifest["project"]["signatures"]
                else:
                    manifest["project"]["signatures"] = signatures
                invalid = {**bundle, "manifest.json": encode(manifest)}
                with self.assertRaisesRegex(ValueError, "指纹"):
                    validate_bundle(invalid)

    def test_four_platform_lifecycle_preserves_other_skills_and_project_ai_files(self):
        from snapshot import capture

        repo = project(self.local.home / "synthetic-workspace")
        for name in (".codex", ".claude", ".kiro", ".qoder", ".trellis", ".cairn"):
            folder = repo / name
            folder.mkdir(exist_ok=True)
            (folder / "existing.md").write_bytes(b"project context")
        for name in ("AGENTS.md", "CLAUDE.md"):
            (repo / name).write_bytes(b"project instruction")
        before = capture(repo)

        sentinels = {}
        for platform in PLATFORMS:
            sibling = entry(self.local, platform).parent.with_name("some-other-skill") / "SKILL.md"
            sentinels[sibling] = f"other {platform}".encode()
        for config in (".codex/AGENTS.md", ".claude/CLAUDE.md", ".kiro/steering/other.md"):
            sentinels[self.local.home / config] = b"user-owned configuration\r\n"
        for file, body in sentinels.items():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(body)

        self.cli("register", "--path", repo, "--apply")
        flags = [value for name in PLATFORMS for value in ("--platform", name)]
        self.install(*flags, "--apply")
        doctor = self.cli("doctor", "--cwd", repo)
        self.assertTrue(doctor["project"]["active"])
        self.assertEqual(len(doctor["project"]["signatures"]), 6)
        self.cli("uninstall", "--apply")
        self.assertEqual({path: path.read_bytes() for path in sentinels}, sentinels)
        self.assertEqual(before, capture(repo))

    def test_candidate_requires_core_and_router_index(self):
        from release import reviewed_source, validate_bundle

        _, bundle = reviewed_source(self.version1, self.first)
        for field, missing in (("base", "standards/priority.md"), ("tags", "java")):
            with self.subTest(field=field):
                manifest = json.loads(bundle["manifest.json"])
                if field == "base":
                    manifest[field].remove(missing)
                else:
                    del manifest[field][missing]
                with self.assertRaisesRegex(ValueError, "索引"):
                    validate_bundle({**bundle, "manifest.json": encode(manifest)})
