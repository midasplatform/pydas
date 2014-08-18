#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
# Library:   pydas
#
# Copyright 2010 Kitware Inc. 28 Corporate Drive,
# Clifton Park, NY, 12065, USA.
#
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 ( the "License" );
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################

import os
import sys

from setuptools import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

packages = ['pydas']
requires = ['requests']

setup(name='pydas',
      version='0.2.36',
      description='Upload data to a Midas-based application with Python.',
      long_description=open('README.rst').read(),
      author='Patrick Reynolds',
      author_email='patrick.reynolds@kitware.com',
      url='http://github.com/midasplatform/pydas',
      packages=packages,
      install_requires=requires,
      license='Apache 2.0',
      zip_safe=True,
      classifiers=(
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
      ),
      )
