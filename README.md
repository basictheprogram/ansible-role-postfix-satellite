# ansible-role-postfix-satellite

[![Ansible Galaxy](https://img.shields.io/badge/ansible--galaxy-realtime.postfix__satellite-blue)](https://galaxy.ansible.com/ui/standalone/roles/realtime/postfix_satellite/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)
[![Ansible Version](https://img.shields.io/badge/ansible--core-%3E%3D2.20-red)](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)
[![GitHub last commit](https://img.shields.io/github/last-commit/basictheprogram/ansible-role-postfix-satellite)](https://github.com/basictheprogram/ansible-role-postfix-satellite/commits/master)

Configures Postfix as a **satellite (relay-only)** mail system. The role installs
Postfix, deploys `/etc/postfix/main.cf` from a template, manages `/etc/aliases`,
and optionally configures SASL authentication and a generic address rewrite table
for relaying through a smarthost such as Amazon SES, SendGrid, or an internal mail
relay.

Targets **Postfix 3.6+**. The generated configuration does not use any parameters
removed in 3.6 (`tls_random_source`, `smtp_use_tls`).

## Supported Platforms

| OS | Versions |
|----|----------|
| Ubuntu | 22.04 (jammy), 24.04 (noble), 26.04 (resolute) |
| Debian | 13 (trixie) |
| RHEL / Rocky / AlmaLinux | 9, 10 |

## Requirements

- Ansible >= 2.20
- Collection: `community.general` (required for the `alternatives` module on
  RedHat/EL), declared in `requirements.yml`

Install it before running the role:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Role Variables

### Top-level defaults (`defaults/main.yml`)

| Variable | Default | Description |
|----------|---------|-------------|
| `postfix_conf` | `{}` | Main configuration dict — see below |
| `postfix_satellite_packages` | `[]` | Base package list override |
| `postfix_satellite_sasl_packages` | `[]` | SASL package list override |
| `sasl_conf` | `[]` | Files locked to mode 0600 (populated by `vars/<OsFamily>.yml`) |

### Required

All Postfix configuration is supplied through the `postfix_conf` dictionary.
The following keys are always required:

| Key | Description |
|-----|-------------|
| `postfix_conf.myhostname` | The FQDN of this host (`myhostname` in main.cf) |
| `postfix_conf.myorigin` | The domain appended to unqualified addresses |
| `postfix_conf.admin_email` | Destination for postmaster/root/daemon aliases |

### Optional keys in `postfix_conf`

| Key | Default | Description |
|-----|---------|-------------|
| `relayhost` | — | Smarthost FQDN. Omit to send directly. |
| `relayport` | `25` | Port for the smarthost connection |
| `mydestination` | `localhost` | Domains delivered locally (satellite roles typically leave this minimal) |
| `inet_protocols` | `all` | `ipv4`, `ipv6`, or `all` |
| `compatibility_level` | `3.6` | Postfix compatibility level |
| `lmtp_host_lookup` | — | Set any value to enable `lmtp_host_lookup = native` |
| `smtp_host_lookup` | — | Set any value to enable `smtp_host_lookup = native` |
| `smtp_tls` | — | Set any truthy value to enable TLS for outbound delivery |
| `smtp_sasl` | — | List of SASL credentials (see below). Implicitly enables TLS. |
| `generic_table` | — | List of address rewrite rules (see below) |

### SASL authentication (`postfix_conf.smtp_sasl`)

Provide a list of credentials. When this key is present, SASL auth is enabled,
`smtp_tls_security_level` is set to `encrypt`, and a `sasl_passwd` map is
deployed and postmap'd.

```yaml
postfix_conf:
  smtp_sasl:
    - username: "AKIAIOSFODNN7EXAMPLE"
      password: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

### Generic address rewrite table (`postfix_conf.generic_table`)

Rewrites envelope sender addresses before delivery. Each entry needs a `pattern`
and a `result`:

```yaml
postfix_conf:
  generic_table:
    - pattern: "@internal.example.com"
      result: "noreply@example.com"
```

### Package variables (defined in `vars/<OsFamily>.yml`)

These are internal role variables set per OS family. Override them in your
inventory only if your environment requires non-standard packages.

| Variable | Description |
|----------|-------------|
| `postfix_satellite_packages` | Base Postfix packages to install |
| `postfix_satellite_sasl_packages` | SASL library packages (installed only when `smtp_sasl` is defined) |
| `generic_table` | Path to the generic rewrite table |
| `sasl_passwd` | Path to the SASL password map |
| `sasl_conf` | List of SASL files to lock down to mode 0600 |

## Task Flow

1. **Preflight** — fails fast before touching the host if:
   - ansible-core is older than 2.20
   - the OS family isn't Debian or RedHat
   - `postfix_conf` is undefined, empty, or missing a required key
   - `relayport` is set but isn't a valid port number
   - `smtp_sasl` is set without `smtp_tls`, or an entry is missing
     `username`/`password`
   - a `generic_table` entry is missing `pattern` or `result`
2. Gather OS-specific variables from `vars/<OsFamily>.yml`
3. Install Postfix (and SASL packages, if `smtp_sasl` is set)
4. Deploy `/etc/postfix/main.cf` (restarts Postfix)
5. Configure `/etc/aliases` (runs `newaliases`)
6. Deploy and postmap the SASL password map, and lock down its
   permissions (only if `smtp_sasl` is set)
7. Deploy the generic address rewrite table (only if `generic_table`
   is set)
8. Fix chroot jail ownership/permissions — runs on every play, not
   gated by any variable

## Example Playbooks

### Minimal — relay without authentication

```yaml
- hosts: servers
  become: true
  vars:
    postfix_conf:
      admin_email: ops@example.com
      myhostname: "{{ inventory_hostname }}"
      myorigin: example.com
      relayhost: smtp.example.com
      relayport: "25"
  roles:
    - role: realtime.postfix_satellite
```

### Full — relay through Amazon SES with SASL and address rewriting

```yaml
- hosts: servers
  become: true
  vars:
    postfix_conf:
      admin_email: ops@example.com
      myhostname: "{{ inventory_hostname }}"
      myorigin: example.com
      relayhost: email-smtp.us-east-1.amazonaws.com
      relayport: "587"
      compatibility_level: "3.6"
      smtp_tls: true
      smtp_sasl:
        - username: "{{ ses_smtp_username }}"
          password: "{{ ses_smtp_password }}"
      generic_table:
        - pattern: "@internal.example.com"
          result: "noreply@example.com"
  roles:
    - role: realtime.postfix_satellite
```

## Amazon SES Notes

- Use the SES SMTP interface on port 587 (STARTTLS).
- Generate SMTP credentials from the SES console (IAM-based; **not** your AWS
  access key). See the
  [SES SMTP credentials guide](https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html).
- Verify your sending domain and configure DKIM before moving out of the SES
  sandbox.
- The `generic_table` rewrite is useful to ensure all outbound mail presents a
  verified From address.

## Testing

Tests use [Molecule](https://ansible.readthedocs.io/projects/molecule/) with
Docker, against a fixed platform matrix — Ubuntu 22.04/24.04/26.04, Debian 13,
and EL 9/10 (represented by the `rockylinux9`/`rockylinux10` images, since no
generic EL geerlingguy image exists).

```bash
# Fast iteration on a single scenario run
molecule converge
molecule verify

# Full exercise across all platforms in the matrix
molecule test
```

## License

MIT

## Author

[Bob Tanner](https://github.com/basictheprogram) —
[Real Time Enterprises Inc.](https://www.real-time.com)
