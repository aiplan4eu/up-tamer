#!/usr/bin/env python3

from setuptools import setup # type: ignore
import setuptools.command.install
import subprocess


class InstallCommand(setuptools.command.install.install):
  '''Custom install command.'''

  def run(self):
    subprocess.call('./install.sh')
    setuptools.command.install.install.run(self)



upf_commit = 'e5cfd58ac83cfd96556fd4461517b4c1a5330bfb'


long_description=\
'''============================================================
    UPF_TAMER
 ============================================================

    upf_tamer is a small package that allows an exchange of
    equivalent data structures between UPF and Tamer.
    It automatically considers the different programming languages.
'''


setup(name='upf_tamer',
      version='0.0.1',
      description='upf_tamer',
      author='AIPlan4EU Organization',
      author_email='aiplan4eu@fbk.eu',
      url='https://aiplan4eu.fbk.eu/',
      packages=['upf_tamer'],
      install_requires=[f'upf@git+https://github.com/aiplan4eu/upf.git@{upf_commit}'],
      cmdclass={
        'install': InstallCommand,
        },
      license='APACHE'
     )
