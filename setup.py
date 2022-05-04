#!/usr/bin/env python3

from setuptools import setup # type: ignore
import up_tamer


long_description=\
'''
 ============================================================
    UP_TAMER
 ============================================================

    up_tamer is a small package that allows an exchange of
    equivalent data structures between unified_planning and Tamer.
    It automatically considers the different programming languages.
'''

setup(name='up_tamer',
      version=up_tamer.__version__,
      description='up_tamer',
      author='FBK Tamer Development Team',
      author_email='tamer@fbk.eu',
      url='https://tamer.fbk.eu',
      packages=['up_tamer'],
      install_requires=['pytamer==0.1.1'],
      python_requires='>=3.7',
      license='APACHE'
)
