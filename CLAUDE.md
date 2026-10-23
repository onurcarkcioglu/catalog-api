# catalog-api — project rules for Claude Code

Answer the user in **Turkish**. Code, tests and docs stay in English unless the file already uses Turkish
(`.gitlab-ci.yml` and script comments are Turkish without diacritics; keep them that way).

## What this repository is
A FastAPI catalog service and, more importantly, its 16-job secure delivery chain (including `ss-tools`, which fetches the shared scripts) (`.gitlab-ci.yml`, job names
in brackets): lint [`lint`] → unit-test [`unit-test`] → hadolint [`hadolint`] → exception file [`exceptions-check`] →
Checkov [`checkov-helm`] → gitleaks [`secret-scan`] → Semgrep [`sast`] → Trivy fs [`sca`] →
SonarQube Quality Gate [`sonarqube`] → Kaniko build [`build`] → Trivy image + SBOM [`image-scan`] →
cosign sign [`sign`] → Helm deploy by digest [`deploy`] → OWASP ZAP [`dast`] → DefectDojo [`defectdojo-upload`].
Platform details: `~/securestream` (read its `CLAUDE.md`).

Every branch push runs eleven jobs (all except the five below; `build` pushes an image to the registry).
`sonarqube`, `sign`, `deploy`, `dast` and `defectdojo-upload` run only on `main` (protected tokens); a red
Quality Gate stops `sign` and `deploy`. `main` is also mirrored read-only to GitHub.

## How to work here
- Local loop: `. .venv/bin/activate && ruff check . && ruff format --check . && pytest -q`.
- Security requirements are written as tests (input validation, security headers, admin auth). A new
  requirement gets a test first; never delete or weaken a security test to make CI pass.
- Shared security jobs, helper scripts and every CI tool image digest come from `securestream/ci-templates` at a
  **tag** (`include` ref and `SS_CI_REF` are one YAML anchor). Change images or shared jobs there (`scripts/pin-images.sh`,
  new tag), then raise the tag here. `ss-tools` (`.pre`) fetches the scripts into `.ss-tools/`.
- Helm chart: keep non-root, read-only rootfs, dropped capabilities, seccomp, NetworkPolicy with no egress.
  `helm lint deploy/helm/catalog-api -f deploy/helm/catalog-api/ci/lint-values.yaml` before committing
  (the chart renders only with an image digest).
- Scanner exceptions go to `security/exceptions.yaml` (time-boxed, max 90 days), never inline suppressions.
- Before pushing, run the checks available locally: the local loop, `helm lint`, and
  `gitleaks git --log-opts=HEAD --redact .`. Semgrep and Trivy are not installed on ss-mgmt; say so instead of
  claiming they passed. After pushing, watch the pipeline to green (command in `~/securestream/CLAUDE.md`).
- Commits: one conventional prefix (`feat`, `fix`, `docs`, `ci`, `chore`), message in Turkish without diacritics
  like the existing history. No day or sprint labels: the message describes the change.

## Security rules — non-negotiable
1. Never read or print secret values (CI variables, Vault data, kubeconfigs, tokens). The admin API key exists
   only in Vault; tests use a fake key via `monkeypatch`.
   kubectl reads the kubeconfig itself, so file deny rules do not cover it: never `kubectl get/describe secret`,
   use `-o yaml` / `-o json` only as `claude-readonly` and print only the fields you need (env values are visible).
   kubectl only as `claude-readonly` (read-only RBAC, no secrets, no logs/exec; see `~/securestream/CLAUDE.md`):
   never the admin kubeconfig, `--kubeconfig`, `--context`, `--token` or `KUBECONFIG=`. Cluster changes are the human's.
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
