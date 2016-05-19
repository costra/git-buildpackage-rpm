# vim: set fileencoding=utf-8 :
#
# (C) 2015,2016 Guido Günther <agx@sigxcpu.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, please see
#    <http://www.gnu.org/licenses/>

import os

from tests.component import (ComponentTestBase,
                             ComponentTestGitRepository)
from tests.component.deb import DEB_TEST_DATA_DIR

from nose.tools import ok_, eq_

from gbp.scripts.deb.import_dsc import main as import_dsc
from gbp.scripts.deb.buildpackage import main as buildpackage


class TestBuildpackage(ComponentTestBase):
    """Test building a debian package"""

    def check_hook_vars(self, name, vars):
        """
        Check that a hook hat the given vars in
        it's environment.
        This assumes the hook was set too
            printenv > hookname.oug
        """
        env = []
        with open('%s.out' % name) as f:
            env = [line.split('=')[0] for line in f.readlines()]

        for var in vars:
            ok_(var in env, "%s not found in %s" % (var, env))

    def _test_buildpackage(self, pkg, dir, version):
        def _dsc(pkg, version):
            return os.path.join(DEB_TEST_DATA_DIR,
                                dir,
                                '%s_%s.dsc' % (pkg, version))

        dsc = _dsc(pkg, version)
        assert import_dsc(['arg0', dsc]) == 0
        ComponentTestGitRepository(pkg)
        os.chdir(pkg)
        ret = buildpackage(['arg0',
                            '--git-prebuild=printenv > prebuild.out',
                            '--git-postbuild=printenv > postbuild.out',
                            '--git-builder=/bin/true',
                            '--git-cleaner=/bin/true'])
        ok_(ret == 0, "Building the package failed")
        eq_(os.path.exists('prebuild.out'), True)

        self.check_hook_vars('prebuild', ["GBP_BUILD_DIR",
                                          "GBP_GIT_DIR",
                                          "GBP_GIT_DIR",
                                          "GBP_BUILD_DIR"])

        self.check_hook_vars('postbuild', ["GBP_CHANGES_FILE",
                                           "GBP_BUILD_DIR",
                                           "GBP_CHANGES_FILE",
                                           "GBP_BUILD_DIR"])

    def test_debian_buildpackage(self):
        """Test that building a native debian  package works"""
        self._test_buildpackage('git-buildpackage', 'dsc-native', '0.4.14')

    def test_non_native_buildpackage(self):
        """Test that building a native debian  package works"""
        self._test_buildpackage('hello-debhelper', 'dsc-3.0', '2.8-1')

    def test_tag_only(self):
        """Test that only tagging a native debian package works"""
        def _dsc(version):
            return os.path.join(DEB_TEST_DATA_DIR,
                                'dsc-native',
                                'git-buildpackage_%s.dsc' % version)

        dsc = _dsc('0.4.14')
        assert import_dsc(['arg0', dsc]) == 0
        repo = ComponentTestGitRepository('git-buildpackage')
        os.chdir('git-buildpackage')
        repo.delete_tag('debian/0.4.14')  # make sure we can tag again
        ret = buildpackage(['arg0',
                            '--git-tag-only',
                            '--git-posttag=printenv > posttag.out',
                            '--git-builder=touch builder-run.stamp',
                            '--git-cleaner=/bin/true'])
        ok_(ret == 0, "Building the package failed")
        eq_(os.path.exists('posttag.out'), True)
        eq_(os.path.exists('builder-run.stamp'), False)
        self.check_hook_vars('posttag', ["GBP_TAG",
                                         "GBP_BRANCH",
                                         "GBP_SHA1"])
