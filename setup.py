#!/usr/bin/env python
from setuptools import setup

setup(
    name='aquasystems-driver',
    version='0.0.1',
    packages=['aquasystems'],
    description='MQTT Bluetooth Service for Aqua Systems Tap Timer',
    url='https://github.com/sammchardy/aquasystems-driver',
    author='Sam McHardy',
    license='MIT',
    author_email='',
    install_requires=['Adafruit-BluefruitLE', 'hbmqtt'],
    keywords='"aqua systems" yardeen bluetooth "home assistant" "tap timer"',
    classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
