import hashlib
import hmac
import importlib.util
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings

SECRET = "s" * 40
SHA = "a" * 40
BASE_DIR = Path(__file__).resolve().parent.parent


def signed(path, body=b"", secret=SECRET, timestamp=None):
    ts = str(int(time.time()) if timestamp is None else timestamp)
    digest = hmac.new(secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    return {
        "path": path, "data": body, "content_type": "application/json",
        "HTTP_X_DEPLOY_TIMESTAMP": ts, "HTTP_X_DEPLOY_SIGNATURE": f"sha256={digest}",
    }


class DeployEndpointTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        override = override_settings(BASE_DIR=Path(self.tmp.name), DEPLOY_SECRET=SECRET)
        override.enable()
        self.addCleanup(override.disable)

    def trigger(self, **kwargs):
        body = json.dumps({"sha": SHA}).encode()
        return self.client.post(**signed("/hooks/deploy/", body, **kwargs))

    def test_disabled_without_secret(self):
        with override_settings(DEPLOY_SECRET=""):
            self.assertEqual(self.trigger().status_code, 404)

    def test_rejects_missing_wrong_and_stale_signatures(self):
        self.assertEqual(self.client.post("/hooks/deploy/", "{}", content_type="application/json").status_code, 403)
        self.assertEqual(self.trigger(secret="x" * 40).status_code, 403)
        self.assertEqual(self.trigger(timestamp=int(time.time()) - 3600).status_code, 403)

    def test_only_post(self):
        self.assertEqual(self.client.get("/hooks/deploy/").status_code, 405)

    def test_signature_covers_the_body(self):
        request = signed("/hooks/deploy/", json.dumps({"sha": SHA}).encode())
        request["data"] = json.dumps({"sha": "b" * 40}).encode()
        self.assertEqual(self.client.post(**request).status_code, 403)

    def test_invalid_sha_is_refused(self):
        response = self.client.post(**signed("/hooks/deploy/", json.dumps({"sha": "abc; rm -rf /"}).encode()))
        self.assertEqual(response.status_code, 400)

    @mock.patch("landed_cost.deploy.subprocess.Popen")
    def test_valid_call_starts_the_script_detached_without_login(self, popen):
        response = self.trigger()
        self.assertEqual(response.status_code, 202)
        popen.assert_called_once()
        command = popen.call_args.args[0]
        self.assertEqual(command[1:], [str(Path(self.tmp.name) / "scripts" / "deploy_update.py"), SHA])
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertTrue((Path(self.tmp.name) / "deploy.lock").exists())

    @mock.patch("landed_cost.deploy.subprocess.Popen")
    def test_second_call_while_running_is_refused(self, popen):
        self.assertEqual(self.trigger().status_code, 202)
        self.assertEqual(self.trigger().status_code, 409)
        self.assertEqual(popen.call_count, 1)

    @mock.patch("landed_cost.deploy.subprocess.Popen")
    def test_stale_lock_is_replaced(self, popen):
        lock = Path(self.tmp.name) / "deploy.lock"
        lock.write_text("")
        old = time.time() - 3600
        os.utime(lock, (old, old))
        self.assertEqual(self.trigger().status_code, 202)

    @mock.patch("landed_cost.deploy.subprocess.Popen", side_effect=OSError("boom"))
    def test_launch_failure_releases_lock(self, popen):
        self.assertEqual(self.trigger().status_code, 500)
        self.assertFalse((Path(self.tmp.name) / "deploy.lock").exists())

    def test_status_requires_signature_and_reports_state(self):
        self.assertEqual(self.client.post("/hooks/deploy/status/").status_code, 403)
        base = Path(self.tmp.name)
        (base / "deploy_state.json").write_text(json.dumps({"state": "done", "sha": SHA}))
        (base / "deploy.log").write_text("\n".join(f"ligne {i}" for i in range(100)))
        data = self.client.post(**signed("/hooks/deploy/status/")).json()
        self.assertEqual((data["state"], data["sha"]), ("done", SHA))
        self.assertEqual(len(data["log_tail"]), 40)
        self.assertEqual(data["log_tail"][-1], "ligne 99")

    def test_status_when_nothing_ran(self):
        self.assertEqual(self.client.post(**signed("/hooks/deploy/status/")).json()["state"], "idle")


class VersionTests(SimpleTestCase):
    def setUp(self):
        from landed_cost import version

        self.version = version
        version.get_version.cache_clear()
        self.addCleanup(version.get_version.cache_clear)

    @staticmethod
    def git_output(text, code=0):
        return mock.Mock(returncode=code, stdout=text + "\n", stderr="")

    def test_reads_commit_date_and_subject_from_git(self):
        outputs = [self.git_output("de42c9e"), self.git_output("2026-09-25T17:58:00+02:00"), self.git_output("Un titre")]
        with mock.patch("landed_cost.version.subprocess.run", side_effect=outputs):
            info = self.version.get_version()
        self.assertEqual(info, {"short": "de42c9e", "date": "25/09/2026 17:58", "subject": "Un titre"})

    def test_result_is_computed_once(self):
        outputs = [self.git_output("aaaaaaa"), self.git_output("2026-01-02T03:04:05+00:00"), self.git_output("x")]
        with mock.patch("landed_cost.version.subprocess.run", side_effect=outputs) as run:
            self.version.get_version()
            self.version.get_version()
        self.assertEqual(run.call_count, 3)

    def test_unknown_when_git_is_missing_or_fails(self):
        with mock.patch("landed_cost.version.subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(self.version.get_version()["short"], "inconnue")
        self.version.get_version.cache_clear()
        with mock.patch("landed_cost.version.subprocess.run", return_value=self.git_output("", code=128)):
            self.assertEqual(self.version.get_version()["short"], "inconnue")

    def test_version_is_shown_in_the_page_footer(self):
        info = {"short": "abc1234", "date": "25/09/2026 17:58", "subject": "Mon commit"}
        with mock.patch("landed_cost.version.get_version", return_value=info):
            response = self.client.get("/connexion/")
        self.assertContains(response, "Version abc1234 · 25/09/2026 17:58")
        self.assertContains(response, 'title="Mon commit"')


def load_script():
    spec = importlib.util.spec_from_file_location("deploy_update", BASE_DIR / "scripts" / "deploy_update.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeployScriptTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.script = load_script()
        self.script.BASE = self.base

    def state(self):
        return json.loads((self.base / "deploy_state.json").read_text())

    def test_backup_copies_database_and_keeps_only_the_last_ones(self):
        database = sqlite3.connect(self.base / "db.sqlite3")
        database.execute("create table t (x)")
        database.execute("insert into t values (42)")
        database.commit()
        database.close()

        backups = self.base / "backups"
        backups.mkdir()
        for month in range(1, 13):
            (backups / f"db-avant-deploiement-2020{month:02d}01-000000.sqlite3").write_text("vieux")
        self.script.backup_database()

        kept = sorted(backups.glob("db-avant-deploiement-*.sqlite3"))
        self.assertEqual(len(kept), self.script.KEEP_BACKUPS)
        names = [p.name for p in kept]
        self.assertNotIn("db-avant-deploiement-20200101-000000.sqlite3", names)
        self.assertNotIn("db-avant-deploiement-20200301-000000.sqlite3", names)
        self.assertIn("db-avant-deploiement-20200401-000000.sqlite3", names)
        copy = sqlite3.connect(kept[-1])
        self.assertEqual(copy.execute("select x from t").fetchone(), (42,))
        copy.close()

    def test_successful_run_goes_through_all_steps_in_order(self):
        steps = []
        (self.base / "deploy.lock").write_text("")
        with mock.patch.object(self.script, "run", side_effect=lambda step, cmd, **kw: steps.append(step)), \
                mock.patch.object(self.script, "check_commit"), mock.patch.object(self.script, "backup_database"), \
                mock.patch.object(self.script, "reload_app", return_value=True):
            self.assertEqual(self.script.main(SHA), 0)
        self.assertEqual(steps, ["Récupération du code", "Dépendances", "Migrations", "Fichiers statiques"])
        self.assertEqual(self.state()["state"], "done")
        self.assertFalse((self.base / "deploy.lock").exists())

    def test_failure_stops_before_reload_and_releases_lock(self):
        steps = []

        def fake_run(step, command, **kwargs):
            steps.append(step)
            if step == "Migrations":
                raise self.script.DeployError("Migrations : échec (code 1).")

        (self.base / "deploy.lock").write_text("")
        with mock.patch.object(self.script, "run", side_effect=fake_run), \
                mock.patch.object(self.script, "check_commit"), mock.patch.object(self.script, "backup_database"), \
                mock.patch.object(self.script, "reload_app") as reload_app:
            self.assertEqual(self.script.main(SHA), 1)
        self.assertNotIn("Fichiers statiques", steps)
        reload_app.assert_not_called()
        self.assertEqual(self.state()["state"], "failed")
        self.assertIn("Migrations", self.state()["error"])
        self.assertFalse((self.base / "deploy.lock").exists())

    def test_reload_touches_the_wsgi_file_when_configured(self):
        wsgi = self.base / "wsgi.py"
        wsgi.write_text("x")
        old = time.time() - 1000
        os.utime(wsgi, (old, old))
        with mock.patch.dict(os.environ, {"DJANGO_DEPLOY_WSGI_FILE": str(wsgi)}):
            self.assertTrue(self.script.reload_app())
        self.assertGreater(wsgi.stat().st_mtime, old + 500)

    def test_reload_without_wsgi_file_reports_manual_step(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DJANGO_DEPLOY_WSGI_FILE", None)
            self.assertFalse(self.script.reload_app())
