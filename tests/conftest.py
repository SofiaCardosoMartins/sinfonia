# Copyright (c) 2022 Carnegie Mellon University
# SPDX-License-Identifier: MIT

from uuid import UUID

import pytest
import wgconfig.wgexec
from flask import Flask
from geolite2 import geolite2

from sinfonia.deployment_repository import DeploymentRepository
from sinfonia.matchers import match_by_location, match_by_network, match_random, match_resources, match_balance

GOOD_UUID = "00000000-0000-0000-0000-000000000000"
GOOD_CONTENT = """\
chart: example
version: 0.1.0
restricted: false
"""
BAD_UUID = "00000000-0000-0000-0000-000000000001"
BAD_CONTENT = """\
chart: example
"""
RESTRICTED_UUID = "00000000-0000-0000-0000-000000000002"
RESTRICTED_CONTENT = """\
chart: private
version: 0.1.0
"""


@pytest.fixture(scope="session")
def repository(tmp_path_factory):
    repo = tmp_path_factory.mktemp("repository")
    (repo / GOOD_UUID).with_suffix(".yaml").write_text(GOOD_CONTENT)
    (repo / BAD_UUID).with_suffix(".yaml").write_text(BAD_CONTENT)
    (repo / RESTRICTED_UUID).with_suffix(".yaml").write_text(RESTRICTED_CONTENT)
    return DeploymentRepository(repo)


@pytest.fixture(scope="session")
def good_uuid():
    return UUID(GOOD_UUID)


@pytest.fixture(scope="session")
def bad_uuid():
    return UUID(BAD_UUID)


@pytest.fixture(scope="session")
def restricted_uuid():
    return UUID(RESTRICTED_UUID)


@pytest.fixture
def mock_generate_keypair(monkeypatch):
    """wgconfig.wgexec.generate_keypairs mocked so we don't `wg` binary"""
    keypairs = [
        (
            "mHJFze/rYugSqH5y5jYgJmJA+Xn+8GYankWDJx69Ymo=",
            "LaMgyk/jPiVRX1XFhBbbW7RlZQO976ZOcnpjlRIeSCc=",
        ),
        (
            "AB9y9TPUpZRYXdA/VEMmY1vjXN78xnG3W5u0kh+7H3c=",
            "P8+7aAk2FsUYkhX4CvJfFWWThus25+A9AeoIRdeEumU=",
        ),
        (
            "wDKetfz9LiQq1hu4E8x0woPmwFp/Oc6Zt69gglQHsV8=",
            "nyJ86rdfI7nxVk7CBoDV42e6gh6E2EzAbI/dVTGbdjs=",
        ),
    ]

    def generate_keypair():
        return keypairs.pop()

    monkeypatch.setattr(wgconfig.wgexec, "generate_keypair", generate_keypair)


@pytest.fixture(scope="session")
def flask_app():
    app = Flask("test")
    app.config["geolite2_reader"] = geolite2.reader()
    app.config["match_functions"] = [match_by_network, match_by_location, match_random, match_resources, match_balance]
    return app


@pytest.fixture(scope="session")
def example_wgkey():
    return "YpdTsMtb/QCdYKzHlzKkLcLzEbdTK0vP4ILmdcIvnhc="
