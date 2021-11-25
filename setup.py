#!/usr/bin/env python3

from setuptools import setup, find_packages # type: ignore
import setuptools.command.install
import subprocess


class InstallCommand(setuptools.command.install.install):
  '''Custom install command.'''

  def run(self):
    subprocess.call('./install.sh')
    setuptools.command.install.install.run(self)



upf_commit = '6b712922217df6b3e4e78eb8c14c652756b230a7'

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
      author='UPF Team',
      author_email='info@upf.com',
      url='https://aiplan4eu.fbk.eu/',
      packages=['upf_tamer'],
      install_requires=[f'upf @ https://github.com/aiplan4eu/upf.git@{upf_commit}'],
      cmdclass={
        'install': InstallCommand,
        },
      license='APACHE'
     )
