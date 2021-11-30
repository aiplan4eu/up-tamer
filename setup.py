#!/usr/bin/env python3

from setuptools import setup # type: ignore
from setuptools.dist import Distribution
import os
import shutil
import setuptools.command.install
import subprocess
import sys

upf_commit = 'e5cfd58ac83cfd96556fd4461517b4c1a5330bfb'
tamer_commit = 'ed3e21b306a37ac0045c2310ad1e26021f40865f'


long_description=\
'''============================================================
    UPF_TAMER
 ============================================================

    upf_tamer is a small package that allows an exchange of
    equivalent data structures between UPF and Tamer.
    It automatically considers the different programming languages.
'''


def running_under_virtualenv():
    """
    Return True if we're running inside a virtualenv, False otherwise.
    Note: copied from pip.
    """

    if hasattr(sys, 'real_prefix'):
        return True
    elif sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return True

    return False


def solver_install_site(plat_specific=False):
    """Determine solver's install site similarly to pip behaviour on Debian.

    Note: copied from pysmt.
    """

    # install to local user-site, unless in virtualenv or running as root
    default_user = True
    if running_under_virtualenv():
        default_user = False
    try:
        if os.geteuid() == 0:
            default_user = False
    except:
        # getuid/geteuid not supported on windows
        pass

    return package_install_site(user=default_user, plat_specific=plat_specific)


def package_install_site(name='', user=False, plat_specific=False):
    """pip-inspired, distutils-based method for fetching the
    default install location (site-packages path).
    Returns virtual environment or system site-packages, unless
    `user=True` in which case returns user-site (typ. under `~/.local/
    on linux).
    If there's a distinction (on a particular system) between platform
    specific and pure python package locations, set `plat_specific=True`
    to retrieve the former.

    Note: copied from pysmt.
    """

    dist = Distribution({'name': name})
    dist.parse_config_files()
    inst = dist.get_command_obj('install', create=True)
    # NOTE: specifying user=True will create user-site
    if user:
        inst.user = user
        inst.prefix = ""
    inst.finalize_options()

    # platform-specific site vs. purelib (platform-independent) site
    if plat_specific:
        loc = inst.install_platlib
    else:
        loc = inst.install_purelib

    # install_lib specified in setup.cfg has highest precedence
    if 'install_lib' in dist.get_option_dict('install'):
        loc = inst.install_lib

    return loc


class InstallCommand(setuptools.command.install.install):
  '''Custom install command.'''

  def run(self):

    cmds = [
            'rm -rf Tamer Tamer.zip',
            f'wget https://es-static.fbk.eu/people/amicheli/tamer/aiplan4eu/Tamer-{tamer_commit}.zip &> /dev/null',
            f'unzip Tamer-{tamer_commit}.zip &> /dev/null',
            f'rm Tamer-{tamer_commit}.zip']
    for cmd in cmds:
      subprocess.run(cmd, capture_output=True, shell=True)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    bindings_dir = os.path.expanduser(solver_install_site(plat_specific=True))

    shutil.copyfile(os.path.join(dir_path, 'Tamer', 'pytamer.py'), os.path.join(bindings_dir, 'pytamer.py'))
    shutil.copyfile(os.path.join(dir_path, 'Tamer', '_pytamer.so'), os.path.join(bindings_dir, '_pytamer.so'))

    subprocess.run('rm -rf Tamer', shell=True)

    setuptools.command.install.install.run(self)


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
