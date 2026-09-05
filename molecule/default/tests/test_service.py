"""Service and chroot-jail tests for the ansible-role-postfix-satellite Molecule scenario.

Covers role behavior beyond config files and packages: the running service
and the chroot jail file ownership fixed up by "postfix set-permissions".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from testinfra.host import Host


def test_postfix_service_is_running_and_enabled(host: Host) -> None:
    service = host.service("postfix")
    assert service.is_running
    assert service.is_enabled


def test_chroot_resolv_conf_is_owned_by_root(host: Host) -> None:
    f = host.file("/var/spool/postfix/etc/resolv.conf")
    assert f.exists
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
