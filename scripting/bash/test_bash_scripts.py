import http.server
import os
import subprocess
import threading
from pathlib import Path

HERE = Path(__file__).parent

DF_FIXTURE = """Filesystem     1024-blocks      Used Available Capacity Mounted on
/dev/sda1         10000000   9500000    500000      95% /
/dev/sdb1         20000000   2000000  18000000      10% /data
/dev/sdc1         10000000   8000000   2000000      80% /var/log
"""


def run_disk(tmp_path, *args):
    fixture = tmp_path / "df.txt"
    fixture.write_text(DF_FIXTURE)
    env = {**os.environ, "DF_CMD": f"cat {fixture}"}
    return subprocess.run(
        ["bash", HERE / "disk_alert.sh", *args], capture_output=True, text=True, env=env
    )


def test_disk_alert_finds_full_filesystems(tmp_path):
    r = run_disk(tmp_path)
    assert r.returncode == 1
    assert "/dev/sda1 mounted on / is at 95%" in r.stdout
    assert "/var/log" in r.stdout
    assert "/data" not in r.stdout


def test_disk_alert_ok_with_high_threshold(tmp_path):
    r = run_disk(tmp_path, "99")
    assert r.returncode == 0 and r.stdout == ""


def test_disk_alert_rejects_bad_threshold(tmp_path):
    assert run_disk(tmp_path, "abc").returncode == 2


class _Handler(http.server.BaseHTTPRequestHandler):
    calls = 0

    def do_GET(self):  # noqa: N802
        type(self).calls += 1
        self.send_response(200 if type(self).calls >= 3 else 503)
        self.end_headers()

    def log_message(self, *args):
        pass


def test_wait_for_healthy_retries_until_200():
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/healthz"
        r = subprocess.run(
            ["bash", HERE / "wait_for_healthy.sh", url, "5", "1"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert r.returncode == 0, r.stderr
        assert "healthy after 3 attempt(s)" in r.stdout
    finally:
        server.shutdown()


def test_wait_for_healthy_gives_up():
    r = subprocess.run(
        ["bash", HERE / "wait_for_healthy.sh", "http://127.0.0.1:1/", "2", "1"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 1
    assert "unhealthy after 2 attempts" in r.stderr
