# SLSA build type: GitLab CI + Kaniko

This document is the `buildType` of the SLSA v1 provenance that the `sign` job attaches to every `main` image
(`cosign attest --type slsaprovenance1`, predicate from `ci/slsa-provenance.sh`).

## Build

A GitLab CI pipeline on the self-hosted GitLab (`gitlab.securestream.lab`) runs the `build` job on the group
runner (Docker executor, `privileged = false`). Kaniko (maintained fork, pinned by digest) builds `Dockerfile` with
the build argument `PYTHON_IMAGE` (pinned by digest) and pushes the image to `registry.securestream.lab`. The
`sign` job signs the image digest and attaches the CycloneDX SBOM and this provenance with the project's cosign key.

## Fields

| Field | Meaning |
|---|---|
| `externalParameters.source` | Git repository and ref (`git+<project>.git@refs/heads/<branch>`) with the commit SHA |
| `externalParameters.config` | Pipeline definition (`.gitlab-ci.yml`) and the `securestream/ci-templates` tag it includes |
| `externalParameters.buildArgs` | Kaniko build arguments (`PYTHON_IMAGE`, by digest) |
| `internalParameters` | Pipeline id and source, whether the ref is protected |
| `resolvedDependencies` | Source commit, base image digest, Kaniko image digest |
| `runDetails.builder.id` | `https://gitlab.securestream.lab/securestream/gitlab-runner/docker-unprivileged` |
| `runDetails.metadata` | Pipeline URL (`invocationId`), pipeline creation and provenance time |

## What it proves, and what it does not

- The image was built from the named commit by this project's pipeline on the protected `main` branch, with the
  listed pinned inputs, and the record is signed with the key that the cluster trusts. Kyverno checks the signature
  and the source repository before a pod is admitted.
- The provenance is generated and signed inside the pipeline with a key held in a protected CI variable, not by an
  isolated signing service. A compromised job on `main` could forge it. This corresponds to SLSA Build L2
  (hosted build, signed provenance), not L3 (non-forgeable provenance from an isolated builder).
