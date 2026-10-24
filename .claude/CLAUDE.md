<!-- 3c-generated framework_version=2.1.1 generated_at=2026-10-24T07:11:47.550Z input_hash=sha256:0e853a1ad5ead2dd0b0ba6dcd020739de972fe8a1af1ac0dc8258b761241a625 -->

# 3C — Coding Standards

This file is loaded by Claude Code at session start. Keep it under **200 lines** and within **150 RFC-2119 directives** (counted by `\b(MUST|SHALL|SHOULD|MAY)(\s+NOT)?\b`). Move detail into `.claude/rules/` files when this file grows.

## Architecture

This is a **static, single-file prototype** with no server and no import graph between modules, so there are no layers to enforce and `.3c/architecture.yaml` stays inert on purpose.

- `index.html` is generated: it MUST be changed through `tools/build.py` (patches over `backup/AI Center X prototype.html` plus `tools/why.css` and `tools/why.js`), never by hand.
- Each film is one standalone file, `simulation/<slug>/<Name>.html`, built from `simulation/_template/`; `simulation/_template/README.md` is its technical contract.
- A film MUST NOT depend on another film or on files outside its folder, apart from the pinned CDN scripts the template names.

## Testing

Tests are written test-first (TDD):

- A failing test MUST exist before the implementation that satisfies it.
- The minimal change needed to pass the test SHOULD be made; only then refactor.
- The red / green / refactor cycle MUST NOT be skipped on new film behaviour or on build steps in `tools/build.py`.
- Test names SHOULD describe behaviour, not implementation.

> Source: Kent Beck, *Test-Driven Development by Example* (Addison-Wesley, 2003).

Tests run on Python Playwright (Chromium, SwiftShader WebGL):

- Test files MUST be named `<slug>_test.py` and live under `test/`.
- Every film MUST pass the shared `test/film_controls_test.py`; checks specific to one film go in that film's own `test/<slug>_test.py`.
- Tests MUST NOT depend on each other; ordering MUST NOT affect outcomes.
- A test MUST exit non-zero on any failure, so the aggregate scripts can gate on it.
- Node Playwright is not installed; `test/controls-test.cjs` (Village Film) is kept for reference and is not part of the suite.

Aggregate scripts (`package.json`): `npm run build`, then `npm run check` (`verify` for `index.html`, `test:films` for every film).

## Security

Security follows the OWASP Top 10:2025 baseline:

- **A01 Broken Access Control** — every request boundary MUST enforce authorisation server-side; deny-by-default.
- **A02 Security Misconfiguration** — security defaults MUST be hardened (no debug endpoints, no default credentials).
- **A03 Software Supply Chain Failures** — third-party dependencies MUST be pinned; SBOMs SHOULD be produced; build pipelines SHOULD be reproducible.
- **A04 Cryptographic Failures** — sensitive data MUST be encrypted at rest (AES-256) and in transit (TLS 1.3+).
- **A05 Injection** — all input crossing a trust boundary MUST be validated and parameterised before use in queries, shell, or templates.
- **A06 Insecure Design** — threat modelling SHOULD inform new features touching auth, payments, or PII.
- **A07 Authentication Failures** — passwords MUST use modern adaptive hashing; sessions MUST be invalidated on logout and password change.
- **A08 Data Integrity Failures** — deserialisation of untrusted data MUST NOT execute code; signatures SHOULD be verified for software updates.
- **A09 Logging and Monitoring Failures** — security-relevant events MUST be logged; logs MUST NOT contain secrets or PII in cleartext.
- **A10 Mishandling of Exceptional Conditions** — error paths MUST fail closed; unexpected exceptions MUST NOT leak stack traces or implementation detail to users.

> Source: OWASP Foundation, *OWASP Top 10:2025* — https://owasp.org/Top10/2025/.

Scope in this repo: there is no server, login or stored personal data, so A01, A04 and A07 apply only if one is introduced. What applies today:

- **A03** — every CDN script MUST carry a pinned version and an SRI `integrity` hash (Three.js r128 from cdnjs does).
- **A05** — `innerHTML` MUST receive only literals from the prototype's own data, never URL, hash or other user-controlled input.

## Project exceptions

- File-size cap: `index.html` and `simulation/**/*.html` are exempt from the 500-line cap in `quality/file-size-and-comments`. `index.html` is generated, and each film is standalone by contract, so there is no seam to split along. Build tools and tests stay under the cap.

## General

- Code MUST follow existing conventions in the surrounding codebase.
- Public functions and classes SHOULD have a one-sentence purpose comment when the name alone does not say it.
- Comments SHOULD explain *why* the code is shaped this way; the code itself explains *what*.
- Secrets MUST NOT appear in committed files.

<!-- 3C:DYNAMIC-LOAD-ANCHOR -->

<!-- 3C:RULES-BEGIN schema=1 generated_at=2026-10-24T07:11:47.907Z rules_count=0 -->

Rule packs kept on disk, loaded by Claude Code from `.claude/rules/` rather than copied here: quality/file-size-and-comments, quality/test-layering, security/cwe-top-25-2025, security/owasp-top-10, ux/tone-and-manner.
<!-- 3C:RULES-END -->

<!--
This file was generated by 3C v2.1.1.
The team's steward owns ongoing edits via PR review against `.claude/`.
See branding/BRANDING.md §Governance for the steward role.
-->
