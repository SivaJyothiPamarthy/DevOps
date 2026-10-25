# DevOps Interview Kit — Stockholm Edition 🇸🇪

A practical DevOps interview preparation repo built around what Stockholm tech
companies (Spotify, Klarna, King, Ericsson, H&M Group, Volvo Cars, Epidemic
Sound, Truecaller, Kry/Livi, Voi, SEB, Zettle and others) typically ask.

It contains **a realistic take-home task with a complete, working solution**,
plus the questions and live scenarios you are likely to meet in later rounds.

## What's inside

| Path | What it is |
|------|------------|
| [`task/TASK.md`](task/TASK.md) | The take-home assignment (read this first, try it yourself) |
| [`solution/`](solution/) | Full reference solution: app, tests, Docker, Kubernetes, Helm-free Kustomize, Terraform, monitoring |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | CI/CD pipeline for the solution (lint → test → build → scan → deploy) |
| [`docs/stockholm-companies.md`](docs/stockholm-companies.md) | Company-by-company stack and interview style |
| [`docs/interview-questions.md`](docs/interview-questions.md) | 60+ questions with model answers, by topic |
| [`docs/live-troubleshooting.md`](docs/live-troubleshooting.md) | "Something is broken, fix it" scenarios with step-by-step solutions |
| [`docs/system-design.md`](docs/system-design.md) | DevOps-flavoured system design rounds with answer outlines |
| [`scripting/`](scripting/) | Bash/Python coding tasks that appear in screening rounds, with solutions and tests |

## Typical Stockholm interview process

1. **Recruiter / HR screen** (30 min) — motivation, salary expectations
   (SEK/month), notice period (often 3 months in Sweden), right to work.
2. **Hiring manager chat** (45 min) — past projects, team fit, "lagom" collaboration style.
3. **Technical screen** (60 min) — Linux, networking, containers, scripting.
4. **Take-home or live pairing** (2–4 h) — like [`task/TASK.md`](task/TASK.md).
5. **Deep dive / system design** (60–90 min) — walk through your solution, then scale it.
6. **Values / culture round** — Swedish companies weight this heavily:
   flat hierarchy, consensus, autonomy, work–life balance, blameless culture.

## Quick start (run the solution locally)

```bash
cd solution/app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q                     # run tests
python -m app.main            # http://localhost:8080/healthz

# or with Docker
cd solution
docker compose up --build     # app + Prometheus + Grafana
```

## How to use this repo for practice

1. Read `task/TASK.md`, set a 4-hour timer, and build your own version.
2. Compare with `solution/` and read `solution/DESIGN.md` — it is written the
   way you'd present it in the follow-up interview.
3. Drill `docs/interview-questions.md` out loud.
4. Have a friend pick a random scenario from `docs/live-troubleshooting.md`.
