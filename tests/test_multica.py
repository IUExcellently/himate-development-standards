"""Multica 原生导入的离线数据契约与规则继承用例。"""
import json
from pathlib import Path
import tempfile
import unittest

from support import ROOT, project, source
from detect_project import MANIFEST
from local_state import Local, encode
from release import reviewed_source


class MulticaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox = tempfile.TemporaryDirectory(prefix="multica-pack-test-")
        cls.addClassCleanup(cls.sandbox.cleanup)
        cls.root = Path(cls.sandbox.name).resolve()
        cls.repo = cls.root / "source"
        cls.revision = source(cls.repo)
        cls.version, cls.files = reviewed_source(cls.repo, cls.revision)

    def test_native_archive_keeps_the_complete_reviewed_runtime(self):
        from multica import build_archive, read_archive, summary

        blob = build_archive(self.files)
        self.assertEqual(build_archive(dict(reversed(list(self.files.items())))), blob)
        self.assertEqual(read_archive(blob), self.files)
        result = summary(self.files)
        self.assertEqual(result["version"], MANIFEST["version"])
        self.assertEqual(result["supporting_files"], len(self.files) - 1)
        self.assertTrue(all(name in self.files for name in MANIFEST["backend"]))

    def test_unsafe_and_secret_payloads_are_refused(self):
        from multica import verify_files

        for name, body in (("../manifest.json", b"x"), (".env", b"x"),
                           ("references/SKILL.md", b"nested"), ("references/LICENSE.md", b"license"),
                           ("references/payload.md", b"a" * (1024 * 1024 + 1)),
                           ("references/secret.md", b"api_key = '" + b"a" * 30 + b"'"),
                           ("references/truncated.md", b"abc\0def")):
            with self.subTest(name=name), self.assertRaises(ValueError):
                verify_files({**self.files, name: body})

    def test_planning_never_replaces_other_skill_bindings(self):
        from multica import plan_binding

        other = [{"id": "other", "name": "unrelated", "enabled": True}]
        owned = {"id": "ours", "name": "himate-development-standards"}
        archive = "bundle.skill"
        self.assertEqual(plan_binding([], None, "worker", other, self.files, archive, workspace="target")["state"], "import")
        self.assertEqual(plan_binding([owned], None, "worker", other, self.files, archive, workspace="target")["state"], "inspect-existing")
        evidence = {
            **owned, "content": self.files["SKILL.md"].decode(), "files": [
                {"path": path, "content": data.decode()} for path, data in self.files.items() if path != "SKILL.md"
            ],
        }
        add = plan_binding([owned], evidence, "worker", other, self.files, archive, workspace="target")
        self.assertEqual(add["command"][3:6], ["agent", "skills", "add"])
        self.assertEqual(add["preserve_bindings"], ["other"])
        bound = [*other, {**owned, "enabled": True}]
        self.assertEqual(plan_binding([owned], evidence, "worker", bound, self.files, archive, workspace="target")["state"], "already-bound")
        self.assertEqual(plan_binding([owned], evidence, "worker", bound, self.files, archive, workspace="target",
                                      remove=True)["state"], "remove-one-in-ui")
        self.assertEqual(plan_binding([owned], evidence, "worker", other, self.files, archive, workspace="target",
                                      remove=True)["state"], "not-bound")
        self.assertEqual(plan_binding(None, None, "worker", other, self.files, archive, workspace="target")["state"], "inventory-unavailable")

    def test_version_drift_does_not_get_an_automatic_binding_plan(self):
        from multica import compare, plan_binding

        owned = {"id": "ours", "name": "himate-development-standards"}
        differing = json.loads(self.files["manifest.json"])
        differing["version"] = "3.0.9"
        changed = {**self.files, "manifest.json": encode(differing)}
        self.assertEqual(compare(self.files, changed)["state"], "different")
        self.assertIn("manifest.json", compare(self.files, changed)["changed"])
        evidence = {**owned, "content": changed["SKILL.md"].decode(), "files": [
            {"path": path, "content": data.decode()} for path, data in changed.items() if path != "SKILL.md"
        ]}
        plan = plan_binding([owned], evidence, "worker", [], self.files, "bundle.skill", workspace="target")
        self.assertEqual(plan["state"], "revision-different")
        self.assertNotIn("command", plan)

    def test_runtime_worktrees_and_roles_independently_route_rules(self):
        from resolve_rules import resolve

        temp = tempfile.TemporaryDirectory(prefix="multica-agent-test-")
        self.addCleanup(temp.cleanup)
        path = Path(temp.name).resolve()
        repo = project(path / "daemon-worktree")
        outside = project(path / "unregistered")
        expected = {
            "写 Controller": "standards/backend/03-api-design.md",
            "SQL 查询优化": "standards/backend/05-sql-guidelines.md",
            "调 HikariCP": "standards/backend/06-database-schema.md",
            "局部 CSS": "standards/frontend-styles.md",
        }
        for role in ("lead", "engineer", "reviewer"):
            home = path / role
            home.mkdir()
            local = Local(home)
            local.state.mkdir()
            local.registry.write_bytes(encode({"schema_version": 1, "roots": [str(repo)]}))
            for task, rule in expected.items():
                with self.subTest(role=role, task=task):
                    result = resolve(repo / "backend", task, local=local)
                    self.assertIn(rule, result["rules"])
                    self.assertEqual(resolve(
                        repo, task, loaded=result["rules"], local=local
                    )["rules"], [])
            self.assertEqual(resolve(outside, "SQL", local=local)["rules"], [])

    def test_approval_and_conflict_require_a_human(self):
        from resolve_conflict import decide

        self.assertEqual(decide(dependency_change=True), "request-dependency-approval")
        self.assertEqual(decide(material=True), "request-user-decision")

    def test_role_templates_use_one_core_entry(self):
        folder = ROOT / "integrations" / "multica"
        core = (folder / "agent-instructions.md").read_text(encoding="utf-8")
        marker = "<!-- BEGIN HIMATE DEVELOPMENT STANDARDS -->"
        self.assertEqual(core.count(marker), 1)
        for name in ("standards/dependency-policy.md", "standards/priority.md"):
            self.assertIn(name, core)
            self.assertTrue((ROOT / name).is_file())
        for role in ("lead", "engineer", "reviewer"):
            addendum = (folder / f"{role}-instructions.md").read_text(encoding="utf-8")
            self.assertNotIn(marker, addendum)
            self.assertIn("自己" if role == "engineer" else "独立", addendum)

    def test_missing_or_ambiguous_inventory_never_proposes_overwrite(self):
        from multica import plan_binding

        same_name = "himate-development-standards"
        ambiguous = [{"id": "one", "name": same_name}, {"id": "two", "name": same_name.upper()}]
        for inventory, expected in ((None, "inventory-unavailable"), (ambiguous, "ambiguous")):
            result = plan_binding(inventory, None, "agent", [], self.files, "bundle.skill", workspace="target")
            self.assertEqual(result["state"], expected)
            self.assertFalse(result["execute"])
            self.assertNotIn("command", result)

    def test_url_extras_need_explicit_fingerprint_and_workspace(self):
        from multica import fingerprint, plan_binding

        owned = {"id": "ours", "name": "himate-development-standards", "workspace_id": "target"}
        native = {**self.files, "README.md": b"URL import also includes source documentation"}
        exported = {**owned, "content": native["SKILL.md"].decode(), "files": [
            {"path": name, "content": content.decode()} for name, content in native.items() if name != "SKILL.md"
        ]}
        args = ([owned], exported, "worker", [], self.files, "bundle.skill")
        blocked = plan_binding(*args, workspace="target")
        self.assertEqual(blocked["state"], "review-url-extras")
        self.assertNotIn("command", blocked)
        selected = plan_binding(*args, workspace="target", reviewed_extras=fingerprint(native))
        self.assertEqual(selected["command"][:3], ["multica", "--workspace-id", "target"])
        with self.assertRaisesRegex(ValueError, "工作区"):
            plan_binding(*args, workspace="unrelated", reviewed_extras=fingerprint(native))

    def test_workspace_evidence_rejects_unsafe_paths_and_invalid_shapes(self):
        from multica import workspace_files

        with self.assertRaisesRegex(ValueError, "完整内容"):
            workspace_files([])
        for name in ("/tmp/extra.md", "../extra.md", "references/../extra.md",
                     "C:/extra.md", "references\\extra.md", "skill.md"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                workspace_files({"content": "entry", "files": [{"path": name, "content": "body"}]})

    def test_runtime_receipt_requires_the_complete_declared_file_set(self):
        from multica import fingerprint, runtime_evidence

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            archive = {"SKILL.md": b"entry"}
            exported = {**archive, "README.md": b"extra"}
            (path / "SKILL.md").write_bytes(archive["SKILL.md"])
            partial = runtime_evidence(folder, archive, exported)
            self.assertEqual(partial["comparison"]["missing"], ["README.md"])
            self.assertIsNone(partial["receipt_prefix"])
            (path / "README.md").write_bytes(exported["README.md"])
            result = runtime_evidence(folder, archive, exported)
            self.assertEqual(result["scope"], "workspace-declared-files")
            self.assertEqual(result["receipt_prefix"], fingerprint(exported)[:12])
            partial_scope = runtime_evidence(folder, archive)
            self.assertEqual(partial_scope["scope"], "archive-declared-files")
