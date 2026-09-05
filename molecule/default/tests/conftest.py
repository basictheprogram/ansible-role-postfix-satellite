"""Session-scoped pytest fixtures for the ansible-role-postfix-satellite Molecule scenario.

No shared fixtures are needed: this role's config paths are fixed across
every supported OS family (see _data.py), so there is no OS-varying value
worth computing once and sharing across test files.
"""

from __future__ import annotations
