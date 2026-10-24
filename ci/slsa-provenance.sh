#!/bin/sh
# SLSA v1 build provenance predicate (https://slsa.dev/provenance/v1) for the image built in this pipeline.
# `sign` writes it to provenance.json and attaches it with `cosign attest --type slsaprovenance1`; the subject
# (image digest) is added by cosign. Only public CI variables are used; no secret goes into the predicate.
# POSIX sh (the cosign image has no bash/jq). Local test: tests/test_slsa_provenance.py.
# Usage: ci/slsa-provenance.sh > provenance.json
set -eu

: "${CI_SERVER_URL:?}" "${CI_PROJECT_URL:?}" "${CI_COMMIT_SHA:?}" "${CI_COMMIT_REF_NAME:?}" "${CI_PIPELINE_ID:?}"
: "${CI_PIPELINE_URL:?}" "${CI_PIPELINE_CREATED_AT:?}" "${CI_PIPELINE_SOURCE:?}" "${CI_COMMIT_REF_PROTECTED:?}"
: "${PYTHON_IMAGE:?}" "${KANIKO_IMAGE:?}" "${SS_CI_REF:?}"

# Values are URLs, refs, ids and digests; reject anything that would need JSON escaping
for v in "$CI_SERVER_URL" "$CI_PROJECT_URL" "$CI_COMMIT_SHA" "$CI_COMMIT_REF_NAME" "$CI_PIPELINE_ID" \
  "$CI_PIPELINE_URL" "$CI_PIPELINE_CREATED_AT" "$CI_PIPELINE_SOURCE" "$CI_COMMIT_REF_PROTECTED" \
  "$PYTHON_IMAGE" "$KANIKO_IMAGE" "$SS_CI_REF"; do
  case $v in
    *[!A-Za-z0-9:/._@+=-]*) echo "unexpected character in CI value: $v" >&2; exit 1 ;;
  esac
done

# name@sha256:<hex> -> name, hex (pinned images only)
image_name() { printf '%s' "${1%@sha256:*}"; }
image_digest() {
  d=${1##*@sha256:}
  case $d in
    "$1" | *[!0-9a-f]*) echo "image is not pinned by digest: $1" >&2; exit 1 ;;
  esac
  printf '%s' "$d"
}
PY_NAME=$(image_name "$PYTHON_IMAGE"); PY_DIGEST=$(image_digest "$PYTHON_IMAGE")
KANIKO_NAME=$(image_name "$KANIKO_IMAGE"); KANIKO_DIGEST=$(image_digest "$KANIKO_IMAGE")
FINISHED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SOURCE="git+${CI_PROJECT_URL}.git@refs/heads/${CI_COMMIT_REF_NAME}"

cat <<EOF
{
  "buildDefinition": {
    "buildType": "${CI_SERVER_URL}/securestream/catalog-api/-/blob/main/docs/slsa-build-type.md",
    "externalParameters": {
      "source": { "uri": "${SOURCE}", "digest": { "gitCommit": "${CI_COMMIT_SHA}" } },
      "config": { "path": ".gitlab-ci.yml", "ciTemplatesRef": "${SS_CI_REF}" },
      "buildArgs": { "PYTHON_IMAGE": "${PYTHON_IMAGE}" }
    },
    "internalParameters": {
      "pipelineId": "${CI_PIPELINE_ID}",
      "pipelineSource": "${CI_PIPELINE_SOURCE}",
      "protectedRef": "${CI_COMMIT_REF_PROTECTED}"
    },
    "resolvedDependencies": [
      { "uri": "${SOURCE}", "digest": { "gitCommit": "${CI_COMMIT_SHA}" } },
      { "uri": "docker://${PY_NAME}", "digest": { "sha256": "${PY_DIGEST}" } },
      { "uri": "docker://${KANIKO_NAME}", "digest": { "sha256": "${KANIKO_DIGEST}" } }
    ]
  },
  "runDetails": {
    "builder": { "id": "${CI_SERVER_URL}/securestream/gitlab-runner/docker-unprivileged" },
    "metadata": {
      "invocationId": "${CI_PIPELINE_URL}",
      "startedOn": "${CI_PIPELINE_CREATED_AT}",
      "finishedOn": "${FINISHED}"
    }
  }
}
EOF
