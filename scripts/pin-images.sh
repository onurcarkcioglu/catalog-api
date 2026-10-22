#!/usr/bin/env bash
# CI arac imajlarini ss-runner'da cekip .gitlab-ci.yml'deki yer tutuculari digest ile degistirir.
set -euo pipefail
RUNNER=ubuntu@10.10.10.11
declare -A IMAGES=(
  [__PYTHON__]="python:3.12-slim"
  [__GITLEAKS__]="ghcr.io/gitleaks/gitleaks:v8.30.1"
  [__SEMGREP__]="semgrep/semgrep:1.180.0"
  [__TRIVY__]="aquasec/trivy:0.76.0"
  [__KANIKO__]="martizih/kaniko:v1.28.6-debug"
)
for key in "${!IMAGES[@]}"; do
  ref="${IMAGES[$key]}"
  digest=$(ssh "$RUNNER" "sudo docker pull -q '$ref' >/dev/null && sudo docker inspect --format '{{index .RepoDigests 0}}' '$ref'")
  pinned="${ref}@${digest#*@}"
  sed -i "s|${key}|${pinned}|" .gitlab-ci.yml
  echo "OK  $pinned"
done
