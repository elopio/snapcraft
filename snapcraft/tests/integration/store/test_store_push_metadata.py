# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2017 Canonical Ltd
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

import os
import subprocess

from testtools.matchers import Contains, FileExists

from snapcraft.tests import integration


class PushMetadataTestCase(integration.StoreTestCase):

    def test_without_login(self):
        self.run_snapcraft('snap', 'basic')
        snap_file_path = 'basic_0.1_{}.snap'.format('all')
        self.assertThat(snap_file_path, FileExists())

        error = self.assertRaises(
            subprocess.CalledProcessError,
            self.run_snapcraft, ['push', snap_file_path])
        self.assertIn('No valid credentials found. Have you run "snapcraft '
                      'login"?', str(error.output))

    def test_with_login(self):
        # Make a snap
        self.addCleanup(self.logout)
        self.login()

        # Change to a random name and version.
        name = self.get_unique_name()
        version = self.get_unique_version()
        self.copy_project_to_cwd('basic')
        self.update_name_and_version(name, version)

        self.run_snapcraft('snap')

        # Register the snap
        self.register(name)

        # Push the snap
        snap_file_path = '{}_{}_{}.snap'.format(name, version, 'all')
        self.assertThat(os.path.join(snap_file_path), FileExists())
        output = self.run_snapcraft(['push-metadata', snap_file_path])
        expected = "Pushing metadata to the Store (force=False)"
        self.assertThat(output, Contains(expected))
        expected = "The metadata has been pushed"
        self.assertThat(output, Contains(expected))
