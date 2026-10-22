# Security Policy

This repository is a portfolio / lab project. It is not a production service.

## Reporting a vulnerability

If you find a security issue in the code, the pipeline or the Helm chart, please **do not open
a public issue**. Use GitHub's **"Report a vulnerability"** button (Security tab → Advisories)
to send a private report. I aim to acknowledge reports within 7 days.

## Scope

- In scope: application code, `.gitlab-ci.yml`, Helm chart, scripts in this repository.
- Out of scope: the lab infrastructure itself (it is not reachable from the internet).

## What is never in this repository

Private keys, tokens, kubeconfigs and other secrets. They live in HashiCorp Vault, Ansible
Vault or protected CI variables. Every commit is scanned by gitleaks; the full history was
scanned again before this mirror was made public.
