"""Shared test constants for the ansible-role-postfix-satellite Molecule scenario.

Postfix's own file layout is fixed across every OS family this role supports
(Debian and RedHat/EL both use /etc/postfix and /etc/aliases) -- there is no
per-family config directory to compute, so this drops CONFIG_DIR_BY_FAMILY
from the packaged skeleton.
"""

from __future__ import annotations

# 1. OS-family detection.
REDHAT_DISTROS: frozenset[str] = frozenset({"redhat", "centos", "rocky", "almalinux", "fedora"})

# 2. Packages this role should install, per OS family. The molecule fixture
# sets postfix_conf.smtp_sasl, so the SASL packages are installed alongside
# the base package in every scenario run -- see vars/Debian.yml and
# vars/RedHat.yml.
DEBIAN_PACKAGES: list[str] = [
    "postfix",
    "libsasl2-2",
    "libsasl2-modules",
    "libsasl2-modules-db",
]
REDHAT_PACKAGES: list[str] = [
    "postfix",
    "s-nail",
    "cyrus-sasl",
    "cyrus-sasl-plain",
]

# 3. Config files this role renders. Fixed absolute paths -- see
# templates/postfix_main_cf.j2, templates/aliases.j2, and vars/<OsFamily>.yml
# for sasl_passwd/generic_table. All four exist in the test environment
# because the fixture sets smtp_tls, smtp_sasl, and generic_table.
CONFIG_FILES: list[str] = [
    "/etc/postfix/main.cf",
    "/etc/aliases",
    "/etc/postfix/sasl/sasl_passwd",
    "/etc/postfix/generic",
]
