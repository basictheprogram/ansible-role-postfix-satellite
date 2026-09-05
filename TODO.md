# TODO — ansible-role-postfix-satellite

Items flagged during the `ansible-sync-role` pass (2026-09-05) that were
surfaced but not resolved in this session. Nothing here should be assumed
fixed just because the sync ran.

## Decide-later items

* **`files/.gitignore` is orphaned.** Nothing under `tasks/` references it
  via `copy:`/`template:`/etc. It's the same file previously flagged for a
  `file-contents-sorter` pre-commit failure — but the real question is
  whether it should exist here at all, not just whether it's sorted.
  Options: wire it in (if some file-deployment use case was intended and
  never implemented), or remove it (if it's stray content with no purpose).

* **`smtp_tls_CAfile` is hardcoded to the Debian CA bundle path.**
  `templates/postfix_main_cf.j2` always renders
  `smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt` whenever
  `smtp_sasl` is defined, regardless of OS family. On RedHat/EL that path
  doesn't exist (the correct one is under `/etc/pki/...`, populated by
  `update-ca-trust` — see the handler fix below). This doesn't break
  `molecule converge` (Postfix doesn't validate the file exists at
  config-render time, only when actually opening a TLS connection), so it
  wasn't caught by the new EL9/EL10 test coverage. A real EL deployment
  with SASL configured would fail TLS certificate verification against its
  relay host until this is made OS-family-aware, the same way the
  `Update ca-certificates` handler now is.

* **No `meta/argument_specs.yml` exists.** Not required, but would let
  `ansible-doc` and IDE tooling validate `postfix_conf`'s shape. Not
  created in this session since Step 4 only calls for fixing placeholder
  content in an existing file, not authoring a new one.

* **No `LICENSE` file exists**, despite `meta/main.yml` and `README.md`
  both declaring MIT. Step 5b (stacking a second copyright line) didn't
  apply because there's nothing to stack onto. Consider adding one if this
  role is meant to be redistributed standalone.

* **`issue_tracker_url` was set to the GitHub remote**
  (`github.com/basictheprogram/ansible-role-postfix-satellite`), but this
  repo also has a `gitlab.real-time.com` remote and *which one is the
  actual canonical push target has been an open question all session* —
  raised twice, answered "don't push yet" both times. If `gitlab` turns
  out to be canonical, `issue_tracker_url` in `meta/main.yml` should move
  to `https://gitlab.real-time.com/ansible-roles/postfix-satellite/-/issues`.

## Shared-infrastructure defects found while syncing (out of scope to fix here)

* **`roles/_template/.gitignore` contains a stray `zzz.diff` entry** and
  is not itself alphabetically sorted (fails the same `file-contents-sorter`
  pre-commit hook this role now uses). This affects every role synced from
  the template, not just this one — worth fixing at the source rather than
  per-role.
* **The `ansible-sync-role` skill's own `assets/molecule-requirements.txt`
  is not alphabetically sorted** (`molecule>=24.0.0` sorts before
  `molecule-plugins[docker]>=23.5.0` in the packaged file, which is
  backwards). Same category of issue, same recommendation.

## Testing

* **A live `molecule converge` could not be run at all in this session's
  environment**, and this is a pre-existing issue, not something
  introduced by this sync. `molecule` (tried both 26.8.0 and 24.2.0) and
  `molecule-plugins[docker]` crash during config loading with
  `AttributeError: 'NoneType' object has no attribute 'inventory_file'`
  before any container is created — reproduced identically against both
  the newly-synced 6-platform `molecule.yml` *and* the original,
  unmodified pre-sync file restored from git history, so this is not a
  molecule.yml content bug. The most likely cause is that this machine's
  Python (Homebrew 3.14.7, very new) isn't yet well-supported by current
  `molecule`/`molecule_plugins` releases; no older Python (3.12/3.13) was
  available on this machine to confirm. Whoever next has access to a more
  conventional Python version (3.11 or 3.12) should retry
  `molecule converge` before trusting that this role's test suite
  actually runs end-to-end — everything in this sync was verified
  statically (`ansible-lint`, `pre-commit run --all-files`, `ruff`) but
  **not** via a real container run.
* Once molecule actually runs: only a single-platform target (`ubuntu2204`)
  was even attempted, to avoid spinning up all 6 privileged systemd
  containers in one go before confirming the tooling worked at all. The
  full 6-platform `molecule test` (Ubuntu 22.04/24.04/26.04, Debian 13,
  EL 9/10 via rockylinux9/rockylinux10) has **not** been run end-to-end.
* EL 9/10 have no generic geerlingguy Docker image; the molecule matrix
  represents them via `rockylinux9`/`rockylinux10` instead (per
  `scripts/platform-data.json`'s own guidance). If geerlingguy ever
  publishes a native EL or AlmaLinux 10 image, revisit
  `molecule/default/molecule.yml`.
