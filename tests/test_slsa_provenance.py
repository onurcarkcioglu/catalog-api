"""ci/slsa-provenance.sh: valid SLSA v1 predicate, pinned inputs, refuses unsafe values."""

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PY = "python:3.12-slim@sha256:" + "a" * 64
KANIKO = "martizih/kaniko:v1.28.6-debug@sha256:" + "b" * 64
BASE_ENV = {
    "CI_SERVER_URL": "https://gitlab.securestream.lab",
    "CI_PROJECT_URL": "https://gitlab.securestream.lab/securestream/catalog-api",
    "CI_COMMIT_SHA": "0123456789abcdef0123456789abcdef01234567",
    "CI_COMMIT_REF_NAME": "main",
    "CI_PIPELINE_ID": "100",
    "CI_PIPELINE_URL": "https://gitlab.securestream.lab/securestream/catalog-api/-/pipelines/100",
    "CI_PIPELINE_CREATED_AT": "2026-10-24T12:00:00Z",
    "CI_PIPELINE_SOURCE": "push",
    "CI_COMMIT_REF_PROTECTED": "true",
    "PYTHON_IMAGE": PY,
    "KANIKO_IMAGE": KANIKO,
    "SS_CI_REF": "v1.1.0",
}


def run_script(env):
    # Fixed argv, absolute interpreter: no user-controlled input reaches the command line
    return subprocess.run(
        ["/bin/sh", "ci/slsa-provenance.sh"],
        cwd=REPO,
        env={"PATH": os.environ["PATH"], **env},
        capture_output=True,
        text=True,
    )


def run(**overrides):
    return run_script({**BASE_ENV, **overrides})


def test_predicate_is_valid_slsa_v1():
    result = run()
    assert result.returncode == 0, result.stderr
    pred = json.loads(result.stdout)
    definition, details = pred["buildDefinition"], pred["runDetails"]
    source = definition["externalParameters"]["source"]
    assert (
        source["uri"]
        == "git+https://gitlab.securestream.lab/securestream/catalog-api.git@refs/heads/main"
    )
    assert source["digest"]["gitCommit"] == BASE_ENV["CI_COMMIT_SHA"]
    assert (
        details["builder"]["id"]
        == "https://gitlab.securestream.lab/securestream/gitlab-runner/docker-unprivileged"
    )
    digests = [d["digest"] for d in definition["resolvedDependencies"]]
    assert {"sha256": "a" * 64} in digests and {"sha256": "b" * 64} in digests
    assert details["metadata"]["invocationId"].endswith("/pipelines/100")


def test_unpinned_image_is_refused():
    result = run(PYTHON_IMAGE="python:3.12-slim")
    assert result.returncode != 0
    assert "not pinned by digest" in result.stderr


@pytest.mark.parametrize("value", ['main"injected', "main branch", "main\nx"])
def test_values_needing_escaping_are_refused(value):
    result = run(CI_COMMIT_REF_NAME=value)
    assert result.returncode != 0
    assert result.stdout == ""


def test_missing_variable_is_refused():
    env = dict(BASE_ENV)
    del env["CI_COMMIT_SHA"]
    result = run_script(env)
    assert result.returncode != 0
