# Copyright 2018 Red Hat Inc.
# Copyright 2016 IBM Corp.
#
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

import functools
import sys
import textwrap

import enum
from oslo_config import cfg
import prettytable

from oslo_upgradecheck._i18n import _


class UpgradeCheckCode(enum.IntEnum):
    """Status codes for the upgrade check command"""

    # All upgrade readiness checks passed successfully and there is
    # nothing to do.
    SUCCESS = 0

    # At least one check encountered an issue and requires further
    # investigation. This is considered a warning but the upgrade may be OK.
    WARNING = 1

    # There was an upgrade status check failure that needs to be
    # investigated. This should be considered something that stops an upgrade.
    FAILURE = 2


UPGRADE_CHECK_MSG_MAP = {
    UpgradeCheckCode.SUCCESS: _('Success'),
    UpgradeCheckCode.WARNING: _('Warning'),
    UpgradeCheckCode.FAILURE: _('Failure'),
}


class UpgradeCheckResult(object):
    """Class used for 'nova-status upgrade check' results.

    The 'code' attribute is an UpgradeCheckCode enum.
    The 'details' attribute is a translated message generally only used for
    checks that result in a warning or failure code. The details should provide
    information on what issue was discovered along with any remediation.
    """

    def __init__(self, code, details=None):
        super(UpgradeCheckResult, self).__init__()
        self.code = code
        self.details = details


class UpgradeCommands(object):
    _upgrade_checks = ()

    def _get_details(self, upgrade_check_result):
        if upgrade_check_result.details is not None:
            # wrap the text on the details to 60 characters
            return '\n'.join(textwrap.wrap(upgrade_check_result.details, 60,
                                           subsequent_indent='  '))

    def check(self):
        """Performs checks to see if the deployment is ready for upgrade.

        These checks are expected to be run BEFORE services are restarted with
        new code. These checks also require access to potentially all of the
        Nova databases (nova, nova_api, nova_api_cell0) and external services
        such as the placement API service.
        :returns: UpgradeCheckCode
        """
        return_code = UpgradeCheckCode.SUCCESS
        # This is a list if 2-item tuples for the check name and it's results.
        check_results = []
        for name, func in self._upgrade_checks:
            result = func(self)
            # store the result of the check for the summary table
            check_results.append((name, result))
            # we want to end up with the highest level code of all checks
            if result.code > return_code:
                return_code = result.code

        # TODO(bnemec): Consider using cliff for this so we can output in
        # different formats like JSON or CSV.
        # We're going to build a summary table that looks like:
        # +----------------------------------------------------+
        # | Upgrade Check Results                              |
        # +----------------------------------------------------+
        # | Check: Cells v2                                    |
        # | Result: Success                                    |
        # | Details: None                                      |
        # +----------------------------------------------------+
        # | Check: Placement API                               |
        # | Result: Failure                                    |
        # | Details: There is no placement-api endpoint in the |
        # |          service catalog.                          |
        # +----------------------------------------------------+
        t = prettytable.PrettyTable([_('Upgrade Check Results')],
                                    hrules=prettytable.ALL)
        t.align = 'l'
        for name, result in check_results:
            cell = (
                _('Check: %(name)s\n'
                  'Result: %(result)s\n'
                  'Details: %(details)s') %
                {
                    'name': name,
                    'result': UPGRADE_CHECK_MSG_MAP[result.code],
                    'details': self._get_details(result),
                }
            )
            t.add_row([cell])
        print(t)

        return return_code


def _add_parsers(subparsers, check_callback):
    upgrade_action = subparsers.add_parser('upgrade')
    upgrade_action.add_argument('check')
    upgrade_action.set_defaults(action_fn=check_callback)


def main(check_callback):
    """Simple implementation of main for upgrade checks

    This can be used in upgrade check commands to provide the minimum
    necessary parameter handling and logic.

    :param check_callback: The check function from the concrete implementation
                           of UpgradeCommands.
    """
    add_parsers = functools.partial(_add_parsers,
                                    check_callback=check_callback)
    opt = cfg.SubCommandOpt('category', handler=add_parsers)
    conf = cfg.ConfigOpts()
    conf.register_cli_opt(opt)
    conf(sys.argv[1:])

    conf.category.action_fn()
