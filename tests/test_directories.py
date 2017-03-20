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

import glob
import os

import testtools


class TestDirectories(testtools.TestCase):
    def test_directories(self):
        releases = [x.split('/')[1] for x in glob.glob('specs/*/')]

        for release in releases:

            if release == 'policy':
                # Policy specs are never "implemented" so they don't need to be
                # nested in the same way.
                continue

            files = os.listdir("specs/%s/" % release)
            valid_names = ['approved', 'implemented']

            for name in files:
                if name.startswith('.'):
                    continue

                self.assertIn(
                    name,
                    valid_names,
                    "Found unexpected file in 'specs/%s', specs should be "
                    "submitted to 'specs/%s/approved'" % (release, release)
                )
