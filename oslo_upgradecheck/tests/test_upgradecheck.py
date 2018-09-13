# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_upgradecheck
----------------------------------

Tests for `upgradecheck` module.
"""

import sys

import mock
from oslotest import base

from oslo_upgradecheck import upgradecheck


class TestUpgradeCheckResult(base.BaseTestCase):

    def test_details(self):
        result = upgradecheck.UpgradeCheckResult(
            upgradecheck.UpgradeCheckCode.SUCCESS,
            'test details')
        self.assertEqual(0, result.code)
        self.assertEqual('test details', result.details)


class TestCommands(upgradecheck.UpgradeCommands):
    def success(self):
        return upgradecheck.UpgradeCheckResult(
            upgradecheck.UpgradeCheckCode.SUCCESS, 'Always succeeds')

    def warning(self):
        return upgradecheck.UpgradeCheckResult(
            upgradecheck.UpgradeCheckCode.WARNING, 'Always warns')

    def failure(self):
        return upgradecheck.UpgradeCheckResult(
            upgradecheck.UpgradeCheckCode.FAILURE, 'Always fails')

    _upgrade_checks = (('always succeeds', success),
                       ('always warns', warning),
                       ('always fails', failure),
                       )


class TestUpgradeCommands(base.BaseTestCase):
    def test_get_details(self):
        result = upgradecheck.UpgradeCheckResult(
            upgradecheck.UpgradeCheckCode.SUCCESS,
            '*' * 70)
        upgrade_commands = upgradecheck.UpgradeCommands()
        details = upgrade_commands._get_details(result)
        wrapped = '*' * 60 + '\n  ' + '*' * 10
        self.assertEqual(wrapped, details)

    def test_check(self):
        inst = TestCommands()
        result = inst.check()
        self.assertEqual(upgradecheck.UpgradeCheckCode.FAILURE, result)


class TestMain(base.BaseTestCase):
    def test_main(self):
        mock_argv = ['test-status', 'upgrade', 'check']
        with mock.patch.object(sys, 'argv', mock_argv, create=True):
            inst = TestCommands()
            result = upgradecheck.main(inst.check)
            self.assertEqual(upgradecheck.UpgradeCheckCode.FAILURE, result)
