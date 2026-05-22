# Claude Code project notes — ansible-role-postfix-satellite

This is an Ansible role that configures Postfix as a **satellite
(relay-only)** mail system. It installs Postfix, deploys
`/etc/postfix/main.cf` from a Jinja2 template, manages
`/etc/aliases`, and optionally configures SASL authentication and a
generic address rewrite table for relaying through a smarthost such
as Amazon SES, SendGrid, or an internal relay.

The role targets **Postfix 3.6+** and **ansible-core 2.20** across
Debian/Ubuntu and RedHat/EL. It is maintained by Real Time
Enterprises, Inc.

---

## Behavioral guidelines

These four rules govern how to work in this repo. They bias toward
caution over speed — for trivial one-liner changes, use judgment.

### 1. Think before writing tasks

**Don't assume. Surface tradeoffs. Ask when uncertain.**

Before adding or changing anything:

* State assumptions explicitly. If a variable could live in
  `defaults/`, `vars/`, or `host_vars`, say which and why before
  choosing. The distinction matters: `vars/` values are internal
  role constants (OS package names, file paths) not meant for
  operator override; `defaults/` values are the public interface.
* If multiple approaches exist (e.g. `ansible.builtin.command` vs
  a purpose-built module), present the tradeoff before choosing.
* If the request is ambiguous (which task file? which template
  block?), name the ambiguity and ask. Don't guess and implement.
* If a simpler approach solves the problem, say so and push back.

### 2. Simplicity first

**Minimum tasks, variables, and template logic that solve the
problem.**

* No new default variables beyond what the task being added
  requires.
* No Jinja2 abstraction for logic used in only one template.
* No `when:` conditions for scenarios that have no test coverage.
* No "future-proofing" of the public interface that wasn't asked
  for.
* If a template block is 20 lines and could be 8, rewrite it.

Ask: would a senior Ansible engineer call this overcomplicated?
If yes, simplify.

### 3. Surgical changes

**Touch only what the request requires. Clean up only your own
mess.**

When editing existing tasks, templates, or defaults:

* Don't reformat adjacent YAML, fix unrelated comments, or clean
  up code that wasn't broken by your change.
* Match the existing style — indentation, quoting, bullet character
  — even if you'd do it differently from scratch.
* If you notice unrelated dead code or stale variables, mention it;
  don't delete it without being asked.

When your change creates orphans:

* Remove `vars`, `when` conditions, or template blocks that YOUR
  change made unreachable.
* Don't remove pre-existing orphans unless explicitly asked.

Every changed line should trace directly to the request.

### 4. Goal-driven execution

**Define the success criteria before starting. Verify before
declaring done.**

Transform requests into verifiable outcomes:

* "Add a preflight assertion" → `molecule converge` passes,
  `molecule verify` passes, `pre-commit run --all-files` is clean.
* "Fix an idempotency bug" → second `molecule converge` reports
  zero changed tasks.
* "Refactor a template" → rendered output on a converged instance
  is identical before and after the refactor.

For multi-step changes, state a brief plan before starting:

    1. Edit template  → verify: rendered main.cf is valid postconf
    2. Add task       → verify: molecule converge green
    3. Add assertion  → verify: molecule verify green
    4. Lint           → verify: pre-commit run --all-files clean

Strong success criteria allow independent verification. Weak
criteria ("make it work") require constant clarification.

---

## Role layout

```
defaults/
  main.yml           # Public interface — operator-overridable
vars/
  main.yml           # Commentary only; no global role vars
  Debian.yml         # Package names and file paths for Debian/Ubuntu
  RedHat.yml         # Package names and file paths for RedHat/EL
tasks/
  main.yml           # Orchestrator — include_tasks dispatch only
  preflight.yml      # Assertions: OS, postfix_conf shape, SASL rules
  debian.yml         # apt install — base + SASL packages
  redhat.yml         # dnf install + alternatives for system MTA
handlers/
  main.yml           # restart/reload postfix, newaliases, postmap
templates/
  postfix_main_cf.j2 # /etc/postfix/main.cf
  aliases.j2         # /etc/aliases
  sasl_passwd.j2     # /etc/postfix/sasl/sasl_passwd
  generic.j2         # /etc/postfix/generic
meta/
  main.yml           # Galaxy metadata, platform matrix, collections
molecule/
  default/
    molecule.yml
    prepare.yml      # apt cache + base packages
    converge.yml     # Runs the role with a full postfix_conf fixture
    verify.yml       # Ansible-verifier assertions
```

## Public interface

All Postfix tuning goes through the single `postfix_conf` dict.
There are no top-level `postfix_satellite_*` knobs for mail
settings — if a consumer needs to tweak something, it goes inside
`postfix_conf`.

The only top-level defaults are:

| Variable | Default | Purpose |
|---|---|---|
| `postfix_conf` | `{}` | Main config dict (see README) |
| `postfix_satellite_packages` | `[]` | Base package override |
| `postfix_satellite_sasl_packages` | `[]` | SASL package override |
| `sasl_conf` | `[]` | Files to lock to 0600 |

Required keys inside `postfix_conf`: `myhostname`, `myorigin`,
`admin_email`. Everything else is optional. See `README.md` for the
full reference.

## Vars vs defaults — the rule

* **`vars/<OsFamily>.yml`** — package names (`postfix`,
  `libsasl2-modules`, etc.) and file paths (`/etc/postfix/sasl/
  sasl_passwd`). These are internal constants. Operators should not
  override them; if they need to they can, but there is no design
  intent to support it.
* **`defaults/main.yml`** — the role's public interface. Values here
  are explicitly supported for operator override via `host_vars`,
  `group_vars`, or playbook vars.

Never put an OS-specific package name in `defaults/`. Never put a
user-facing config key in `vars/`.

## Conventions

* **FQCN everywhere**: `ansible.builtin.*` for core modules,
  `community.general.*` for the `alternatives` module on RedHat/EL.
  The `.ansible-lint` `fqcn-builtins` rule enforces this.
* **Tags**: every task carries `tags: postfix-satellite`. The
  preflight include uses `import_tasks` so the tag is inherited
  statically.
* **`changed_when: false`** on every `ansible.builtin.command` task
  that is inherently idempotent (`postmap`, `newaliases`,
  `postfix set-permissions`, `update-ca-certificates`).
* **`loop_var`** on every loop in this role — use
  `postfix_satellite_item` to avoid shadowing the outer `item` if
  the role is called inside another loop.
* **No debug tasks** in committed code. Use `ansible.builtin.debug`
  locally during development; remove before committing.
* **Secrets**: `postfix_conf.smtp_sasl` entries contain credentials.
  If a task or template ever logs them, add `no_log: true`.
* **Lint**: `.ansible-lint`, `.yamllint`, `.pre-commit-config.yaml`
  define the rules. Run `pre-commit run --all-files` before
  declaring work done.
* **Collection dependency**: `community.general` is declared in
  `meta/main.yml`. Don't add further collection dependencies without
  updating meta.

## Settled decisions — don't re-litigate

* **Satellite-only**: `inet_interfaces = loopback-only`. This role
  is never a receiving MTA. Don't add inbound listener config.
* **Postfix 3.6+**: `smtp_use_tls` and `tls_random_source` are
  removed from the template. Don't reintroduce them. Use
  `smtp_tls_security_level` exclusively.
* **`compatibility_level` defaults to `3.6`**. Don't lower it.
* **SASL requires TLS**: the preflight asserts `smtp_tls` is set
  whenever `smtp_sasl` is defined. Don't remove this check or add a
  bypass.
* **Single `postfix_conf` dict**: all Postfix config flows through
  one dict, not individual top-level variables. Don't add
  `postfix_satellite_relayhost:` or similar flat vars.
* **`postfix set-permissions`** runs unconditionally on every play
  to correct chroot jail ownership. Don't gate it on a variable or
  make it a handler — the whole point is it self-heals on every run.
* **OS-specific vars in `vars/`**, not `defaults/`**: the
  `include_vars` lookup in `tasks/main.yml` reads from `paths:
  ["vars"]`. Don't move those files back to `defaults/`.
* **Ansible verifier** (not testinfra) for molecule. The verify
  playbook uses `ansible.builtin.assert`. Don't migrate to pytest
  unless asked.

## Open questions

If a task touches one of these, leave a `# TODO(open-q):` comment
rather than guessing:

* `verify.yml` contains only a trivial `assert: that: true`. Real
  assertions (postfix is running, main.cf rendered correctly,
  sasl_passwd locked down) have not been written yet.
* EL 10 is declared in `meta/main.yml` but has no molecule scenario.
  RedHat/EL tasks are untested in CI.
* `update-ca-certificates` in the handler is Debian-specific; EL
  uses `update-ca-trust`. The handler will fail silently on EL hosts
  if SASL is configured.

## Testing locally

```bash
# Fast lint pass — run before every commit
pre-commit run --all-files

# Iterate on tasks/templates without full destroy/create
molecule converge
molecule verify

# Full role exercise (slow)
molecule test
```

The default molecule scenario uses
`geerlingguy/docker-ubuntu2004-ansible` (or `MOLECULE_DISTRO` env
override). The `prepare.yml` playbook updates the apt cache and
installs a minimal set of base packages before converge runs.

To test against a different distro:

```bash
MOLECULE_DISTRO=debian12 molecule test
```

---

## Commit message guide

You are an expert Linux systems engineer and professional git commit
message writer. When generating a commit message, follow these steps
exactly.

### Step 1 — Retrieve changes

Run:

    git diff --cached

Analyze the full staged diff. This is the **single source of truth**
for what will be committed.

### Step 2 — Understand the change

Determine:

* The **primary purpose** of the change
* The **type of change** (feature, bug fix, refactor, etc.)
* The **most relevant scope** within the role
* Whether the change introduces a **breaking change** for role
  consumers
* Whether multiple changes should be summarized together

Pay special attention to:

* Changes to `defaults/main.yml` — these define the role's public
  interface
* Changes to handler names, task names, and tags — consumers may
  pin to them
* Changes to `postfix_conf` keys that templates reference
* Changes to `postfix_main_cf.j2` — these affect the rendered
  `main.cf` and may require a postfix restart

If multiple files are modified, identify the **dominant intent**
rather than listing every file.

### Step 3 — Select commit type

Use Conventional Commits:

* `feat` — new task, handler, variable, template, or capability
* `fix` — bug fix or idempotency correction
* `docs` — README, CLAUDE.md, role metadata, inline comments
* `style` — YAML formatting, whitespace, ansible-lint cleanup
* `refactor` — restructure tasks/templates without behavior change
* `perf` — performance improvement (e.g., reduced task runs)
* `test` — molecule scenarios, verify playbook, lint config
* `chore` — galaxy metadata, dependencies, tooling
* `ci` — GitHub Actions, pre-commit hooks

### Step 4 — Determine scope

Infer a scope from the role layout or Postfix subsystem.

Common Ansible role scopes: `tasks`, `handlers`, `templates`,
`defaults`, `vars`, `meta`, `molecule`.

Common Postfix subsystem scopes: `main-cf`, `aliases`, `sasl`,
`tls`, `generic`, `preflight`, `chroot`, `packages`.

Only include a scope when it adds clarity. Prefer the Postfix
subsystem scope for feature-driven changes (e.g.,
`feat(sasl): ...`) and the role-layout scope for structural
changes (e.g., `refactor(tasks): ...`).

### Step 5 — Write the commit message

Format exactly as:

    <type>[optional scope]: <short summary (<=50 chars)>

    <body wrapped at 72 characters>

    [optional footer(s)]

**Subject line rules:**

* Use **imperative mood** ("Add", "Fix", "Update", "Remove")
* Maximum **50 characters**
* Describe the **result**, not the implementation
* Prefer Postfix or Ansible terminology over generic phrasing
  (e.g., "Remove deprecated smtp_use_tls parameter", not
  "Update template")

**Body rules** (required):

Explain **why the change was made**, focusing on:

* What Postfix behavior, log warning, or operational scenario
  motivated it
* What downstream role consumers need to know to upgrade safely
* Any Postfix or Ansible version constraints involved

When helpful, summarize key changes using bullet points.

**Bullet rules:**

* Use `*` (asterisk) for all bullets — never `-` or `•`
* Nested bullets indented with two spaces
* No Markdown formatting of any kind

Example:

    * Remove smtp_use_tls from postfix_main_cf.j2
    * Remove tls_random_source from postfix_main_cf.j2
      * Both parameters were removed in Postfix 3.6

**Ansible-specific expectations:**

* Call out new, renamed, or removed default variables
* Note when handler names, tag names, or public task names change
* Mention idempotency improvements when relevant
* Reference supported platforms when adding OS- or
  distribution-specific tasks
* Flag changes to `meta/main.yml` (galaxy metadata, role
  dependencies, minimum Ansible version, supported platforms)
* Note molecule scenario additions or removals

**Postfix-specific expectations:**

* Distinguish between changes that require a postfix **restart**
  (main.cf, master.cf) vs. changes that take effect immediately
  (aliases, postmap'd lookup tables)
* Note the minimum Postfix version when using new directives
* Call out new lookup tables, transports, or restriction classes
  by name
* Highlight TLS or SASL changes that affect authentication or
  certificate verification
* Note `postfix set-permissions` implications when touching chroot
  paths or file ownership
* Flag changes to `postfix_conf` keys that are referenced in
  preflight assertions — removing a required key is a breaking
  change

### Breaking changes

A change is breaking when it:

* Renames or removes a `defaults/main.yml` variable
* Renames or removes a handler, tag, or public task name
* Changes a default value in a way that alters runtime behavior
* Removes a required key from the `postfix_conf` schema
* Drops support for a Postfix or Ansible version
* Changes `inet_interfaces`, `mydestination`, or
  `smtp_tls_security_level` defaults

If the diff introduces a breaking change:

* Add `!` after the type/scope in the subject
* Include a footer: `BREAKING CHANGE: <description>`

Examples:

    feat(sasl): install SASL packages conditionally
    fix(chroot): run postfix set-permissions every play
    refactor(tasks): move OS vars from defaults to vars
    chore(meta): add EL 10 and Ubuntu 26.04 to platforms
    test(molecule): add prepare.yml for apt cache bootstrap

    fix(main-cf)!: remove smtp_use_tls and tls_random_source

    Postfix 3.6 removed both parameters. Any main.cf still
    containing them generates a warning on every postfix
    operation.

    * Remove smtp_use_tls = yes from postfix_main_cf.j2
    * Remove tls_random_source = dev:/dev/urandom from postfix_main_cf.j2
    * smtp_tls_security_level = encrypt/may already handles TLS policy

    BREAKING CHANGE: main.cf rendered by this role no longer
    contains smtp_use_tls; hosts running Postfix < 3.6 should
    not upgrade to this role version.

### Step 6 — Output rules

Return **only the commit message** — no explanation, no analysis,
no diff, no markdown formatting, no code fences. The output will
be pasted directly into a git commit editor.
