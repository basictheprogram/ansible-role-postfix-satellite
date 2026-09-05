"""Config-file tests for the ansible-role-postfix-satellite Molecule scenario.

Parametrized existence checks over CONFIG_FILES, plus single-purpose
permission and content assertions for what this role actually claims about
its rendered output -- never combine an existence check and a content check
in the same test function.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ._data import CONFIG_FILES

if TYPE_CHECKING:
    from testinfra.host import Host


@pytest.mark.parametrize("filename", CONFIG_FILES)
def test_config_file_exists(host: Host, filename: str) -> None:
    f = host.file(filename)
    assert f.exists
    assert f.is_file


def test_sasl_passwd_is_locked_down(host: Host) -> None:
    f = host.file("/etc/postfix/sasl/sasl_passwd")
    assert f.mode == 0o600


def test_sasl_passwd_db_is_locked_down(host: Host) -> None:
    f = host.file("/etc/postfix/sasl/sasl_passwd.db")
    assert f.exists
    assert f.mode == 0o600


def test_sasl_directory_is_locked_down(host: Host) -> None:
    d = host.file("/etc/postfix/sasl")
    assert d.is_directory
    assert d.mode == 0o700


def test_main_cf_uses_loopback_only(host: Host) -> None:
    f = host.file("/etc/postfix/main.cf")
    assert "inet_interfaces = loopback-only" in f.content_string


def test_main_cf_sets_relayhost(host: Host) -> None:
    f = host.file("/etc/postfix/main.cf")
    assert "relayhost = [relay.localhost]:587" in f.content_string


def test_main_cf_enables_sasl_when_configured(host: Host) -> None:
    f = host.file("/etc/postfix/main.cf")
    assert "smtp_sasl_auth_enable = yes" in f.content_string
    assert "smtp_tls_security_level = encrypt" in f.content_string


def test_aliases_routes_to_admin_email(host: Host) -> None:
    f = host.file("/etc/aliases")
    assert "postmaster:     postmaster@localhost" in f.content_string


def test_generic_table_contains_rewrite_rules(host: Host) -> None:
    f = host.file("/etc/postfix/generic")
    assert "@hostname.example.com" in f.content_string
    assert "@example.com" in f.content_string
