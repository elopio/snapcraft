# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2015-2017 Canonical Ltd
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
import shutil
from textwrap import dedent

from testtools.matchers import Contains, FileExists
import integration_tests


class GitSourceTestCase(integration_tests.GitSourceBaseTestCase):

    def _get_git_revno(self, path, revrange='-1'):
        return subprocess.check_output(
            'git -C {} log {} --oneline | cut -d\' \' -f2'.format(
                path, revrange),
            shell=True, universal_newlines=True).strip()

    def test_pull_git_head(self):
        self.copy_project_to_cwd('git-head')

        self.init_and_config_git()
        self.commit('"1"', allow_empty=True)
        self.commit('"2"', allow_empty=True)

        self.run_snapcraft('pull')
        revno = self._get_git_revno('parts/git/src')
        self.assertEqual('"2"', revno)

        self.run_snapcraft('pull')
        revno = self._get_git_revno('parts/git/src')
        self.assertEqual('"2"', revno)

    def test_pull_git_tag(self):
        self.copy_project_to_cwd('git-tag')

        self.init_and_config_git()
        self.commit('"1"', allow_empty=True)
        self.commit('"2"', allow_empty=True)
        subprocess.check_call(
            ['git', 'tag', 'initial', 'HEAD@{1}'],
            stdout=subprocess.DEVNULL)

        self.run_snapcraft('pull')
        revno = self._get_git_revno('parts/git/src')
        self.assertEqual('"1"', revno)

        self.run_snapcraft('pull')
        revno = self._get_git_revno('parts/git/src')
        self.assertEqual('"1"', revno)

    def test_pull_git_commit(self):
        self.copy_project_to_cwd('git-commit')

        self.init_and_config_git()
        self.commit('"1"', allow_empty=True)
        self.commit('"2"', allow_empty=True)

        # The test uses "HEAD^" so we can only test it once
        self.run_snapcraft('pull')
        revno = self._get_git_revno('parts/git/src')
        self.assertEqual('"1"', revno)

    def test_pull_git_branch(self):
        self.copy_project_to_cwd('git-branch')

        self.init_and_config_git()
        self.commit('"1"', allow_empty=True)
        self.commit('"2"', allow_empty=True)
        subprocess.check_call(
            ['git', 'branch', 'second', 'HEAD@{1}'],
            stdout=subprocess.DEVNULL)
        subprocess.check_call(
            ['git', 'checkout', 'second'],
            stderr=subprocess.DEVNULL)
        self.commit('"3"', allow_empty=True)
        subprocess.check_call(
            ['git', 'checkout', 'master'],
            stderr=subprocess.DEVNULL)

        self.run_snapcraft('pull')
        revno = self._get_git_revno('parts/git/src', revrange='-2')
        self.assertEqual('"3"\n"1"', revno)

        self.run_snapcraft('pull')
        revno = self._get_git_revno('parts/git/src', revrange='-2')
        self.assertEqual('"3"\n"1"', revno)

    def test_pull_git_with_depth(self):
        """Regression test for LP: #1627772."""
        self.copy_project_to_cwd('git-depth')

        self.init_and_config_git()
        self.commit('"1"', allow_empty=True)
        self.commit('"2"', allow_empty=True)

        self.run_snapcraft('pull')


class GitGenerateVersionTestCase(integration_tests.GitSourceBaseTestCase):

    def setUp(self):
        super().setUp()
        self.init_and_config_git()
        os.mkdir('snap')

        with open(os.path.join('snap', 'snapcraft.yaml'), 'w') as f:
            print(dedent("""\
                name: git-test
                version: git
                summary: test git generated version
                description: test git generated version with git hint
                architectures: [amd64]
                parts:
                    nil:
                        plugin: nil
                """), file=f)

        self.add_file(os.path.join('snap', 'snapcraft.yaml'))
        self.commit('snapcraft.yaml added')

    def test_tag(self):
        self.tag('2.0')
        self.run_snapcraft('snap')
        self.assertThat('git-test_2.0_amd64.snap', FileExists())

    def test_tag_with_commits_ahead(self):
        self.tag('2.0')
        open('stub_file', 'w').close()
        self.add_file('stub_file')
        self.commit('new stub file')
        self.run_snapcraft('snap')
        revno = self.get_revno()[:7]
        expected_file = 'git-test_2.0+git1.{}_amd64.snap'.format(revno)
        self.assertThat(expected_file, FileExists())

    def test_no_tag(self):
        self.run_snapcraft('snap')
        revno = self.get_revno()[:7]
        expected_file = 'git-test_0+git.{}_amd64.snap'.format(revno)
        self.assertThat(expected_file, FileExists())

    def test_no_git(self):
        shutil.rmtree('.git')

        exception = self.assertRaises(
            subprocess.CalledProcessError, self.run_snapcraft, ['snap'])
        self.assertThat(
            exception.output,
            Contains('fatal: Not a git repository (or any of the parent '
                     'directories): .git'))
