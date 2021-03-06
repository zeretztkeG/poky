# tinfoil: a simple wrapper around cooker for bitbake-based command-line utilities
#
# Copyright (C) 2012 Intel Corporation
# Copyright (C) 2011 Mentor Graphics Corporation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import logging
import warnings
import os
import sys

import bb.cache
import bb.cooker
import bb.providers
import bb.utils
from bb.cooker import state, BBCooker
from bb.cookerdata import CookerConfiguration, ConfigParameters
import bb.fetch2

class Tinfoil:
    def __init__(self, output=sys.stdout):
        # Needed to avoid deprecation warnings with python 2.6
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Set up logging
        self.logger = logging.getLogger('BitBake')
        console = logging.StreamHandler(output)
        bb.msg.addDefaultlogFilter(console)
        format = bb.msg.BBLogFormatter("%(levelname)s: %(message)s")
        if output.isatty():
            format.enable_color()
        console.setFormatter(format)
        self.logger.addHandler(console)

        self.config = CookerConfiguration()
        configparams = TinfoilConfigParameters(parse_only=True)
        self.config.setConfigParameters(configparams)
        self.config.setServerRegIdleCallback(self.register_idle_function)
        self.cooker = BBCooker(self.config)
        self.config_data = self.cooker.data
        bb.providers.logger.setLevel(logging.ERROR)
        self.cooker_data = None

    def register_idle_function(self, function, data):
        pass

    def parseRecipes(self):
        sys.stderr.write("Parsing recipes..")
        self.logger.setLevel(logging.WARNING)

        try:
            while self.cooker.state in (state.initial, state.parsing):
                self.cooker.updateCache()
        except KeyboardInterrupt:
            self.cooker.shutdown()
            self.cooker.updateCache()
            sys.exit(2)

        self.logger.setLevel(logging.INFO)
        sys.stderr.write("done.\n")

        self.cooker_data = self.cooker.recipecache

    def prepare(self, config_only = False):
        if not self.cooker_data:
            if config_only:
                self.cooker.parseConfiguration()
                self.cooker_data = self.cooker.recipecache
            else:
                self.parseRecipes()

class TinfoilConfigParameters(ConfigParameters):

    def __init__(self, **options):
        self.initial_options = options
        super(TinfoilConfigParameters, self).__init__()

    def parseCommandLine(self):
        class DummyOptions:
            def __init__(self, initial_options):
                for key, val in initial_options.items():
                    setattr(self, key, val)

        return DummyOptions(self.initial_options), None
