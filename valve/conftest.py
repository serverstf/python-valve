# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import errno
import os
import shlex
import socket
import subprocess
import time

import pytest

srcds_instances = {}
if "PYTHON_VALVE_SRCDS" in os.environ:
    valve_srcds = os.environ["PYTHON_VALVE_SRCDS"]
    if os.path.isdir(valve_srcds):
        instances_dir = os.path.join(valve_srcds, "instances")
        if os.path.isdir(instances_dir):
            for path in os.listdir(instances_dir):
                full_path = os.path.join(instances_dir, path)
                if os.path.isdir(full_path):
                    srcds_instances[path] = full_path


def pytest_addoption(parser):
    parser.addoption("--srcds", help="A comma-separated list of "
                                     "SRCDS instances to run tests against")


class SRCDSRunner(object):

    _port = 27015

    def __init__(self, instance):
        self.instance = instance
        self.directory = srcds_instances[instance]
        if sys.platform.startswith("linux"):
            exe = "srcds_run"
        elif sys.platform.startswith("win"):
            exe = "srcds.exe"
        else:
            raise OSError("Platform '{}' not supported".format(sys.platform))
        self.executable = os.path.join(self.directory, exe)
        self.process = None
        self.address = ("127.0.0.1", self._port)
        # SRCDS will bind to port -10 and +10 so might as well give it
        # some 'clearance space'
        self._port += 100

    def run(self):
        """Run the SRCDS instance"""
        envar = "PYTHON_VALVE_SRCDS_" + self.instance.upper()
        if envar in os.environ:
            cmdargs = shlex.split(os.environ[envar])
        else:
            cmdargs = []
        args = ([self.executable] + cmdargs +
                ["-console", "-norestart", "-nohltv", "-dev", "-debug",
                 "-ip", self.address[0], "-port", unicode(self.address[1])])
        self.process = subprocess.Popen(args)
        self._wait_til_ready()

    def _wait_til_ready(self):
        """Waits until the server is ready or timesout (20s)"""
        # A listen TCP socket is created on the address -ip -port
        timeout = time.time() + 20
        while time.time() < timeout:
            try:
                sock = socket.socket(socket.AF_INET,
                                     socket.SOCK_STREAM,
                                     socket.IPPROTO_TCP)
                sock.connect(self.address)
                sock.close()
                return
            except socket.error as exc:
                if exc.errno != errno.ECONNREFUSED:
                    raise
        raise RuntimeError("'{}' didn't start".format(self.instance))

    def _kill(self):
        """Stop the process; forcibly if it doesn't stop within 10 secsonds"""
        try:
            self.process.terminate()
            timeout = time.time() + 10
            while self.process.poll() is None and time.time() < timeout:
                pass
            self.process.kill()
        except OSError as exc:
            if exc.errno not in [errno.ESRCH, errno.EACCES]:
                raise



@pytest.fixture(scope="session", params=srcds_instances.keys())
def srcds(request):
    """Runs the test against a local SRCDS instance

    The fixture returns an object which holds the SRCDS's configuration.

    In order for this to work the environment variable PYTHON_VALVE_SRCDS
    must be set to a directory which contains a further directory 'instances'.
    All tests using this fixture will then be ran against all SRCDS
    installations contained within the 'instances' directory.

    You can restrict the tests to only running for specific SRCDS instances
    via the --srcds options.
    """
    srcds_opt = request.config.getoption("srcds")
    if srcds_opt:
        instances = srcds_opt.split(",")
        if instances == ["all"]:
            pass
        else:
            if request.param not in instances:
                pytest.skip("--srcds={}".format(",".join(instances)))
    else:
        pytest.skip("--srcds not set")
    srcds = SRCDSRunner(request.param)
    request.addfinalizer(srcds._kill)
    srcds.run()
    return srcds
