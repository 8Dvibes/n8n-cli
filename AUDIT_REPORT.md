# n8n-cli QA and Build Audit

Date: 2026-04-03

## Scope

Reviewed all Python modules under `n8n_cli/` plus `README.md` and `pyproject.toml`.

Files reviewed:

- `n8n_cli/__init__.py`
- `n8n_cli/audit.py`
- `n8n_cli/cli.py`
- `n8n_cli/client.py`
- `n8n_cli/community_packages.py`
- `n8n_cli/config.py`
- `n8n_cli/credentials.py`
- `n8n_cli/executions.py`
- `n8n_cli/nodes.py`
- `n8n_cli/projects.py`
- `n8n_cli/source_control.py`
- `n8n_cli/tags.py`
- `n8n_cli/users.py`
- `n8n_cli/variables.py`
- `n8n_cli/webhooks.py`
- `n8n_cli/workflows.py`
- `README.md`
- `pyproject.toml`

## Validation Performed

Source review:

- Read every file above end-to-end.
- Looked for logic errors, missing validation, missing error handling, brittle API assumptions, security concerns, and OSS release gaps.

Behavioral/build checks:

- `python3 -m compileall n8n_cli` succeeded.
- `python3 -m n8n_cli.cli --help` succeeded.
- `python3 -m n8n_cli.cli config --help` succeeded.
- `python3 -m n8n_cli.cli workflows --help` succeeded.
- `python3 -m pip wheel . --no-deps --no-build-isolation -w /tmp/n8n-cli-wheelhouse` succeeded.
- Built wheel contents included all package modules and console entrypoint.

Environment-limited observations:

- `python3 -m build --sdist --wheel` could not be exercised because the `build` package is not installed in this environment.
- `python3 -m pip wheel . --no-deps` with build isolation failed offline because pip tried to fetch `setuptools>=68.0`. That is not a code defect by itself, but it means isolated offline builds are not currently reproducible unless build dependencies are preinstalled.

## Executive Summary

The project is small, readable, and packageable. The CLI parses correctly, imports cleanly, and can build a wheel locally.

The main problems are not syntax/build breakage. They are runtime robustness and release readiness:

- The node catalog can silently poison its own cache when npm is unavailable.
- Scoped community package names are not URL-encoded and will break.
- Webhook testing has multiple brittle assumptions that can send requests to the wrong endpoint or with the wrong method.
- Error handling is inconsistent because low-level modules call `sys.exit()` directly.
- Input validation is too loose for several commands.
- The repository is missing baseline OSS release assets such as `LICENSE`, tests, and CI.

If this were headed to a public 0.1 release, I would treat the first six findings below as pre-release fixes.

## Findings

### High

#### 1. Offline node catalog bootstrap writes and caches an empty catalog

Files:

- `n8n_cli/nodes.py:125-226`

What happens:

- `ensure_catalog()` checks npm on every call.
- If npm is unreachable and there is no existing cache, `latest_versions` becomes `{"n8n-nodes-base": "", "@n8n/n8n-nodes-langchain": ""}`.
- The function still proceeds to “update” and writes a cache with zero nodes.
- That empty cache is then treated as a valid catalog on later runs.

Why this matters:

- First-time users in offline, firewalled, or flaky-network environments get a silently broken `nodes` feature instead of a clear error.
- The failure persists because the bad cache is saved to disk.

Repro used during audit:

- Imported `n8n_cli.nodes` under a temporary `HOME` with no prior cache and called `ensure_catalog(quiet=True)`.
- Result was a persisted catalog with `"node_count": 0` and empty versions.

Recommendation:

- If version lookup fails for all packages and no valid cache exists, raise a recoverable error and do not write cache files.
- If a prior cache exists, keep using it.
- Write cache updates atomically so partial failures do not corrupt state.

#### 2. Scoped npm package names break community package commands

Files:

- `n8n_cli/community_packages.py:41-67`

What happens:

- `get_package()`, `update_package()`, and `uninstall_package()` interpolate the package name directly into the URL path.
- Scoped package names such as `@scope/pkg` become `/community-packages/@scope/pkg` instead of `/community-packages/%40scope%2Fpkg`.

Why this matters:

- Scoped package names are common in npm.
- These commands will hit the wrong route or 404 for valid package names.

Recommendation:

- Percent-encode path segments with `urllib.parse.quote(name, safe="")` before inserting them into endpoint paths.
- Add tests covering scoped names.

#### 3. Webhook test routing is brittle and can generate incorrect requests

Files:

- `n8n_cli/webhooks.py:25-50`
- `n8n_cli/webhooks.py:76-81`
- `n8n_cli/cli.py:807-810`

Problems:

- The command selects the first node whose type contains `"webhook"`, which is ambiguous in multi-webhook workflows.
- It reads the configured webhook method but does not use it by default; the CLI default is always `POST`.
- `--method` accepts arbitrary strings with no validation.
- The webhook base URL is derived with `client.api_url.replace("/api/v1", "")`, which is brittle. Example: `https://example.com/api/v1beta` becomes `https://example.combeta`.

Why this matters:

- Valid workflows can be tested against the wrong node or wrong HTTP method.
- Some deployments with nonstandard API paths will produce malformed webhook URLs.

Recommendation:

- Default to the node’s configured `httpMethod` when `--method` is not supplied.
- Restrict `--method` to valid HTTP verbs.
- Let the user choose a node when multiple webhook nodes exist.
- Derive webhook base URLs structurally, not with substring replacement.

### Medium

#### 4. Transport layer has no explicit timeout and hard-exits on network errors

Files:

- `n8n_cli/client.py:40-93`

Problems:

- `urllib.request.urlopen()` is called without a timeout in the main API client.
- `URLError` causes `print(...); sys.exit(1)` inside the client instead of raising a typed exception.

Why this matters:

- API calls can hang indefinitely.
- Low-level hard exits make the code harder to reuse, harder to test, and inconsistent with the CLI’s top-level error handling.
- `--json` mode cannot produce machine-readable network errors because the client exits before `main()` can format them.

Recommendation:

- Add a sane default timeout and optionally expose it as a config/CLI setting.
- Raise a domain exception for network failures and let `main()` decide formatting and exit code.

#### 5. CLI accepts invalid or contradictory input for multiple commands

Files:

- `n8n_cli/cli.py:515-522`
- `n8n_cli/cli.py:679-683`
- `n8n_cli/cli.py:807-810`
- `n8n_cli/variables.py:51-58`

Confirmed examples:

- `workflows list --active --inactive` is accepted and silently resolves to active-only behavior.
- `variables update <id>` is accepted with neither `--key` nor `--value`, causing an empty update body `{}`.
- `webhooks test --method BOGUS` is accepted.
- Many `--limit` arguments accept zero or negative values and are not validated as positive integers.

Why this matters:

- The CLI looks successful while sending ambiguous or invalid requests.
- Automation gets inconsistent behavior instead of immediate input errors.

Recommendation:

- Use `argparse` mutually exclusive groups for contradictory switches.
- Require at least one field for partial update commands.
- Add `choices=` for HTTP method flags.
- Validate all `--limit` arguments as positive integers.

#### 6. Configuration loading returns a shallow copy of the default config

Files:

- `n8n_cli/config.py:15-31`

What happens:

- `load_config()` returns `DEFAULT_CONFIG.copy()` when no config file exists.
- That is a shallow copy, so nested objects such as `profiles` are shared.

Why this matters:

- In-process mutations can leak into future calls and tests.
- During audit, mutating one loaded config mutated the next call’s “default” config as well.

Recommendation:

- Return a deep copy of the default config.
- Consider isolating config mutation behind a small config object or helper functions instead of sharing raw dicts.

#### 7. `config show` leaks part or all of the API key

Files:

- `n8n_cli/cli.py:70-79`

What happens:

- The command prints `key[:8] + "..."`.
- If the key is shorter than eight characters, this reveals the entire key.
- Even for long keys, exposing a stable prefix is more disclosure than needed.

Why this matters:

- This is avoidable credential exposure in logs, screenshots, shells, and support transcripts.

Recommendation:

- Mask with a fixed placeholder or reveal only a minimal suffix, for example `********abcd`.

#### 8. Error handling is inconsistent because lower layers print and exit directly

Files:

- `n8n_cli/config.py:71-81`
- `n8n_cli/client.py:91-93`
- `n8n_cli/nodes.py:299-317`
- `n8n_cli/webhooks.py:32-58`
- `n8n_cli/webhooks.py:104-116`

What happens:

- Several modules mix business logic with CLI concerns by printing to stderr and calling `sys.exit()`.

Why this matters:

- Hard to unit test.
- Hard to reuse these functions outside the CLI.
- Error formatting is inconsistent between normal commands, `--json` mode, and network failures.

Recommendation:

- Raise exceptions from lower layers.
- Keep printing and exit behavior only in `cli.py`.

#### 9. Documentation has user-visible drift from the actual CLI

Files:

- `README.md:131-143`
- `n8n_cli/cli.py:739-814`

Problems:

- README omits the `nodes` and `webhooks` command groups entirely.
- README documents audit categories as `creds,db,fs,instance,nodes`, while the CLI help and implementation expect `credentials,database,filesystem,instance,nodes`.

Why this matters:

- Users will copy wrong commands from the README.
- Missing documentation is especially costly for discovery-oriented features like `nodes` and `webhooks`.

Recommendation:

- Regenerate or hand-sync the command reference from the parser.
- Add examples for `nodes` and `webhooks`.

#### 10. Config writes are not atomic and only lock down permissions after file creation

Files:

- `n8n_cli/config.py:34-38`

What happens:

- The config file is opened normally, JSON is written, then `chmod(0o600)` is applied afterward.

Why this matters:

- There is a small window where a newly created file may inherit broader permissions from the process umask.
- Interrupted writes can leave a partially written config file behind.

Recommendation:

- Write to a temp file with secure permissions first, then `os.replace()` into place.

### Low

#### 11. Execution duration calculation contains dead code and fragile timestamp parsing

Files:

- `n8n_cli/executions.py:52-69`

Problems:

- `delta = datetime.fromisoformat(s) - datetime.fromisoformat(s)` is a no-op and immediately overwritten.
- Timestamps are truncated to the first 19 characters, which strips timezone and subsecond information.

Why this matters:

- The output is usually fine, but the implementation is confusing and easy to regress.

Recommendation:

- Parse the full timestamp once, handle `Z`/offset-aware forms correctly, and remove the dead line.

#### 12. Minor code quality issues add avoidable maintenance cost

Files:

- `n8n_cli/cli.py:28`
- `n8n_cli/workflows.py:138-147`
- `pyproject.toml:7`
- `n8n_cli/__init__.py:3`

Examples:

- `cmd_health()` assigns `resp` and never uses it.
- `export_workflow()` takes `as_json` but does not use it.
- Version is duplicated in both `pyproject.toml` and `n8n_cli/__init__.py`, which can drift.

Recommendation:

- Remove dead variables/args.
- Use a single version source.

## Security Notes

I did not find an obvious remote-code-execution or credential-exfiltration vulnerability in the current codebase.

The main security-adjacent concerns are:

- Partial API key disclosure in `config show`.
- Config writes are not atomic or pre-secured.
- The node catalog phones home to npm on every use, which has privacy and availability implications for users in restricted environments.

## Open Source Release Readiness

Current repo gaps observed during audit:

- No root `LICENSE` file present, even though README and package metadata declare MIT.
- No `tests/` directory.
- No CI workflow files under `.github/`.
- No `CONTRIBUTING.md`.
- No `CHANGELOG.md`.
- No pre-commit/lint/type-check configuration in the repo root.

Impact:

- Legal ambiguity for downstream users without a bundled license file.
- No automated guardrails for parser behavior, request formatting, cache handling, or release builds.

Recommended minimum release baseline:

- Add `LICENSE`.
- Add unit tests for parser validation, config loading, request URL construction, and node catalog caching.
- Add CI for Python 3.9-3.13 at minimum.
- Add a `CONTRIBUTING.md` with local test/build commands.
- Add a simple changelog and release checklist.

## Suggested Test Matrix

Highest-value automated tests to add first:

1. `nodes.ensure_catalog()` with:
   - no network + no cache
   - no network + existing cache
   - partial package download failure
2. Community package commands with scoped names like `@scope/pkg`.
3. CLI parser validation:
   - `--active` and `--inactive` together should fail
   - `variables update` with no fields should fail
   - invalid webhook method should fail
4. `client._request()` timeout and network-error behavior.
5. `config.load_config()` to verify no shared mutable defaults.
6. `webhooks.test()` URL derivation and multi-webhook selection behavior.

## Priority Fix Order

1. Fix node catalog offline caching behavior.
2. URL-encode community package path segments.
3. Harden webhook testing logic and URL derivation.
4. Move all `sys.exit()`/printing to `cli.py` and add transport timeouts.
5. Tighten parser validation for contradictory or empty inputs.
6. Add `LICENSE`, tests, and CI before public release.

## Overall Assessment

The codebase is a reasonable early beta CLI, not a broken one. The wheel builds, the parser works, and the module layout is easy to follow.

The gap is operational hardening. Right now the project is strongest as a personal/internal tool. Before a wider open source release, it needs tighter input validation, safer failure modes, better offline behavior, and basic release infrastructure.
