# AI Workflow Phase 3B CI Gates And Durable CI Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CI gate wiring and a durable CI evidence contract without product-command execution.

**Architecture:** Closed JSON schemas validate CI capability/status and CI gate results. `workflow_helper.py` evaluates local contract state and fails closed when durable GitHub Actions evidence is unavailable. A GitHub Actions workflow runs static/helper checks only.

**Tech Stack:** Markdown, JSON Schema Draft 2020-12, Python unittest, Bash thin wrappers, GitHub Actions.

## Global Constraints

- Preserve approved Phase 1A / 1B / 2A / 2B / 2C / 3A decisions.
- Phase 1B-3 remains `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`.
- Current `codex-desktop` host remains `null` / `UNPROBED` and `UNSUPPORTED`.
- Do not run Gradle, product tests, application server, Docker Compose, HTTP/API, database, migration, seed, deployment, or infrastructure commands locally.
- Do not create repository `.ai-runs`, non-fixture `artifact-manifest.json`, or finalized non-fixture `run.json`.
- Do not promote registry `VERIFIED` or claim unqualified overall DONE.

## Tasks

- [x] Add failing Phase 3B tests for schema allowlist, CI status, workflow wiring, and fail-closed CI gate.
- [x] Add `ci-capability-status` and `ci-gate-result` schemas plus canonical `ai/ci-capability-status.json`.
- [x] Add `ci_evidence_gate()` and `scripts/ai/ci-evidence-gate.sh`.
- [x] Add `.github/workflows/phase-3b-ci-gates.yml` for helper/static CI checks only.
- [x] Record Issue #12 work logs and policy docs.
- [ ] Run focused and broad verification, then request independent review.
