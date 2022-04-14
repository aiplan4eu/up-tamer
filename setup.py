#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import urllib.request
import setuptools.command.install
from setuptools import setup # type: ignore


tamer_commit = 'fdf4c1f13df939e1aaec8e5c8c383f28c270429c'

long_description=\
'''============================================================
    UP_TAMER
 ============================================================

    up_tamer is a small package that allows an exchange of
    equivalent data structures between unified_planning and Tamer.
    It automatically considers the different programming languages.
'''


class InstallPyTamer(setuptools.command.install.install):
    '''Custom install command.'''

    def run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        url = f'https://es-static.fbk.eu/people/amicheli/tamer/aiplan4eu/pytamer-{tamer_commit}.zip'
        with urllib.request.urlopen(url) as response, open(os.path.join(dir_path, 'pytamer.zip'), 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        shutil.unpack_archive(os.path.join(dir_path, 'pytamer.zip'), os.path.join(dir_path, 'pytamer'))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--find-links", os.path.join(dir_path, 'pytamer'), "pytamer"])
        setuptools.command.install.install.run(self)


setup(name='up_tamer',
      version='0.0.1',
      description='up_tamer',
      author='AIPlan4EU Organization',
      author_email='aiplan4eu@fbk.eu',
      url='https://www.aiplan4eu-project.eu',
      packages=['up_tamer'],
      install_requires=[],
      python_requires='>=3.7',
      cmdclass={
          'install': InstallPyTamer,
      },
      license='APACHE'
)
