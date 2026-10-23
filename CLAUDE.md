# catalog-api — project rules for Claude Code

Answer the user in **Turkish**. Code, tests and docs stay in English unless the file already uses Turkish
(`.gitlab-ci.yml` and script comments are Turkish without diacritics; keep them that way).

## What this repository is
A FastAPI catalog service and, more importantly, its 10-job secure delivery chain (`.gitlab-ci.yml`, job names
in brackets): lint [`lint`] → unit-test [`unit-test`] → gitleaks [`secret-scan`] → Semgrep [`sast`] →
Trivy fs [`sca`] → Kaniko build [`build`] → Trivy image + SBOM [`image-scan`] → cosign sign [`sign`] →
Helm deploy by digest [`deploy`] → OWASP ZAP [`dast`]. Platform details: `~/securestream` (read its `CLAUDE.md`).

Every branch push runs the first seven jobs (including `build`, which pushes an image to the registry).
`sign`, `deploy` and `dast` run only on `main`; `main` is also mirrored read-only to GitHub.

## How to work here
- Local loop: `. .venv/bin/activate && ruff check . && ruff format --check . && pytest -q`.
- Security requirements are written as tests (input validation, security headers, admin auth). A new
  requirement gets a test first; never delete or weaken a security test to make CI pass.
- CI tool images are pinned by digest: change versions only via `scripts/pin-images.sh`.
- Helm chart: keep non-root, read-only rootfs, dropped capabilities, seccomp, NetworkPolicy with no egress.
  `helm lint deploy/helm/catalog-api` before committing.
- Before pushing, run the checks available locally: the local loop, `helm lint`, and
  `gitleaks git --log-opts=HEAD --redact .`. Semgrep and Trivy are not installed on ss-mgmt; say so instead of
  claiming they passed. After pushing, watch the pipeline to green (command in `~/securestream/CLAUDE.md`).
- Commits: one conventional prefix (`feat`, `fix`, `docs`, `ci`, `chore`), message in Turkish without diacritics
  like the existing history. No day or sprint labels: the message describes the change.

## Security rules — non-negotiable
1. Never read or print secret values (CI variables, Vault data, kubeconfigs, tokens). The admin API key exists
   only in Vault; tests use a fake key via `monkeypatch`.
   kubectl reads the kubeconfig itself, so file deny rules do not cover it: never `kubectl get/describe secret`,
   never `-o yaml` / `-o json`. Use `-o wide` or `-o jsonpath=` for the specific non-secret fields you need.
2. Never add `allow_failure`, `--exit-code 0`, `--insecure`, `privileged`, or rule exclusions to make a scan pass.
   A finding is fixed, or documented as an accepted risk with a reason — and the user decides that.
   Existing, deliberate exceptions — do not widen them or copy them to other jobs:
   - `dast` has `allow_failure: exit_codes: [2]` (ZAP WARN only); exit code 1 must keep failing. Never downgrade a
     `FAIL` rule in `zap-rules.tsv` to `WARN`/`IGNORE`.
   - `sign` uses `--tlog-upload=false` / `--insecure-ignore-tlog=true` because the lab has no Rekor; signatures are
     still verified against `cosign.pub`.
3. Ask before pushing to `main` (it deploys to the cluster and publishes to GitHub).
4. Never force-push. Never commit generated reports or CI outputs (everything listed in `.gitignore`:
   `gitleaks.json`, `semgrep.json`, `sbom.cdx.json`, `report.xml`, `image-digest.txt`, `zap-report.*`).
