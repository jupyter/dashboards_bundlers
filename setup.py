# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop

from notebook.services.config import ConfigManager

# Get location of this file at runtime
HERE = os.path.abspath(os.path.dirname(__file__))

# Eval the version tuple and string from the source
VERSION_NS = {}
with open(os.path.join(HERE, 'dashboards_bundlers/_version.py')) as f:
    exec(f.read(), {}, VERSION_NS)

def _install_notebook_extension():
    cm = ConfigManager()
    print('Installing notebook extension')
    cm.update('notebook', { 
        'jupyter_cms_bundlers': {
            'dashboards_local_deploy': {
                'label': 'Local Dashboard',
                'module_name': 'dashboards_bundlers.local_deploy',
                'group': 'deploy'
            },
            'dashboards_php_download': {
                'label': 'PHP Dashboard bundle (.zip)',
                'module_name': 'dashboards_bundlers.php_download',
                'group': 'download'
            }
        }
    })

class InstallCommand(install):
    def run(self):
        install.run(self)
        _install_notebook_extension()

class DevelopCommand(develop):
    def run(self):
        develop.run(self)
        _install_notebook_extension()

setup(
    name='jupyter_dashboards_bundlers',
    author='Jupyter Development Team',
    author_email='jupyter@googlegroups.com',
    description='Plugins for jupyter_cms to deploy and download notebooks as dashboard apps',
    long_description = '''
    This package adds a *Deploy as* and *Download as* menu items for bundling 
notebooks created using jupyter_dashboards as standalone web applications.

See `the project README <https://github.com/jupyter-incubator/dashboards_bundlers>`_
for more information. 
''',   
    url='https://github.com/jupyter-incubator/dashboards_bundlers',
    version=VERSION_NS['__version__'],
    license='BSD',
    platforms=['Jupyter Notebook 4.0.x'],
    packages=[
        'dashboards_bundlers',
        'dashboards_bundlers.local_deploy',
        'dashboards_bundlers.php_download'
    ],
    include_package_data=True,
    install_requires=['jupyter_cms>=0.3.0'],
    cmdclass={
        'install': InstallCommand,
        'develop': DevelopCommand
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ]
)