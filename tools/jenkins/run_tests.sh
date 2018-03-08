#!/bin/bash
#
# Copyright (C) 2015-2018 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Run snapcraft tests.
# This assumes that lxd is properly configured, see the setup lxd job in
# Jenkins.
# Arguments:
#   suite: The test suite to run.

set -ex

if [ "$#" -ne 1 ] ; then
    echo "Usage: "$0" <test>"
    exit 1
fi

test="$1"

pattern="$2"

if [ "$test" = "static" ]; then
    dependencies="apt install -y python3-pip && python3 -m pip install -r requirements-devel.txt"
elif [ "$test" = "tests/unit" ]; then
    dependencies="apt install -y git bzr subversion mercurial rpm2cpio p7zip-full libnacl-dev libsodium-dev libffi-dev libapt-pkg-dev python3-pip squashfs-tools xdelta3 && python3 -m pip install -r requirements-devel.txt -r requirements.txt codecov && apt install -y python3-coverage"
elif [[ "$test" = "tests/integration"* || "$test" = "tests.integration"* ]]; then
    # TODO remove the need to install the snapcraft dependencies due to nesting
    #      the tests in the snapcraft package
    # snap install core exits with this error message:
    # - Setup snap "core" (2462) security profiles (cannot reload udev rules: exit status 2
    # but the installation succeeds, so we just ingore it.
    dependencies="apt install -y bzr git libnacl-dev libsodium-dev libffi-dev libapt-pkg-dev mercurial python3-pip subversion sudo snapd && python3 -m pip install -r requirements-devel.txt -r requirements.txt && (snap install core || echo 'ignored error') && ${SNAPCRAFT_INSTALL_COMMAND:-sudo snap install snaps-cache/snapcraft-pr$TRAVIS_PULL_REQUEST.snap --dangerous --classic}"
else
    echo "Unknown test suite: $test"
    exit 1
fi


function delete_container {
  lxc delete --force test-runner
}


script_path="$(dirname "$0")"
project_path="$(readlink -f "$script_path/../..")"

lxc="/snap/bin/lxc"

trap delete_container EXIT
"$script_path/../travis/run_lxd_container.sh" test-runner

ls
$lxc file push --recursive $project_path test-runner/root/
$lxc exec test-runner -- sh -c "cd snapcraft && ./tools/travis/setup_lxd.sh"
$lxc exec test-runner -- sh -c "cd snapcraft && $dependencies"
$lxc exec test-runner -- sh -c "cd snapcraft && ./runtests.sh $test"

if [ "$test" = "snapcraft/tests/unit" ]; then
    # Report code coverage.
    $lxc exec test-runner -- sh -c "cd snapcraft && python3 -m coverage xml"
    $lxc exec test-runner -- sh -c "cd snapcraft && codecov --token=$CODECOV_TOKEN"
fi

$lxc stop test-runner