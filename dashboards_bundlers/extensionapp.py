# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import errno
import os.path
import sys

from ._version import __version__

from notebook.services.config import ConfigManager
from notebook.nbextensions import (EnableNBExtensionApp, 
    DisableNBExtensionApp, flags, aliases)
    
try:
    from notebook.nbextensions import BaseNBExtensionApp
    _new_extensions = True
except ImportError:
    BaseNBExtensionApp = object
    _new_extensions = False
    
from traitlets.config.application import catch_config_error
from traitlets.config.application import Application

# Make copies to reuse flags and aliases
INSTALL_FLAGS = {}
INSTALL_FLAGS.update(flags)

INSTALL_ALIASES = {}
INSTALL_ALIASES.update(aliases)
del INSTALL_ALIASES['destination']

def makedirs(path):
    '''
    mkdir -p and ignore existence errors compatible with Py2/3.
    '''
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

class ExtensionActivateApp(EnableNBExtensionApp):
    '''Subclass that activates this particular extension.'''
    name = u'jupyter-dashboards-bundlers-extension-activate'
    description = u'Activate the jupyter_dashboards_bundlers extension'

    flags = {}
    aliases = {}

    examples = """
        jupyter dashboards_bundlers activate
    """

    def _classes_default(self):
        return [ExtensionActivateApp, EnableNBExtensionApp]

    def start(self):
        self.log.info("Activating jupyter_dashboards_bundlers JS notebook extensions")
        cm = ConfigManager(parent=self, config=self.config)
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
                },
                'dashboards_server_upload': {
                    'label': 'Dashboard on Jupyter Dashboards Server',
                    'module_name': 'dashboards_bundlers.server_upload',
                    'group': 'deploy'
                },
                'dashboards_server_download': {
                    'label': 'Jupyter Dashboards Server bundle (.zip)',
                    'module_name': 'dashboards_bundlers.server_download',
                    'group': 'download'
                }
            }
        })
        self.log.info("Done.")

class ExtensionDeactivateApp(DisableNBExtensionApp):
    '''Subclass that deactivates this particular extension.'''
    name = u'jupyter-dashboards-bundlers-extension-deactivate'
    description = u'Deactivate the jupyter_dashboards_bundlers extension'

    flags = {}
    aliases = {}

    examples = """
        jupyter dashboards_bundlers deactivate
    """

    def _classes_default(self):
        return [ExtensionDeactivateApp, DisableNBExtensionApp]

    def start(self):
        self.log.info("Deactivating jupyter_dashboards_bundlers JS notebook extensions")
        cm = ConfigManager(parent=self, config=self.config)
        cm.update('notebook', { 
            'jupyter_cms_bundlers': {
                'dashboards_local_deploy' : None,
                'dashboards_php_download' : None,
                'dashboards_server_upload' : None,
                'dashboards_server_download' : None
            }
        })
        self.log.info("Done.")

class ExtensionQuickSetupApp(BaseNBExtensionApp):
    """Installs and enables all parts of this extension"""
    name = "jupyter dashboards_bundlers quick-setup"
    version = __version__
    description = "Installs and enables all features of the dashboards_bundlers extension"

    def start(self):
        self.argv.extend(['--py', 'dashboards_bundlers'])
        
        from jupyter_cms import bundlerapp
        enable = bundlerapp.EnableNBBundlerApp()
        enable.initialize(self.argv)
        enable.start()

class ExtensionQuickRemovalApp(BaseNBExtensionApp):
    """Disables and uninstalls all parts of this extension"""
    name = "jupyter dashboards_bundlers quick-remove"
    version = __version__
    description = "Disables and removes all features of the dashboards_bundlers extension"

    def start(self):
        self.argv.extend(['--py', 'dashboards_bundlers'])
        
        from jupyter_cms import bundlerapp
        enable = bundlerapp.DisableNBBundlerApp()
        enable.initialize(self.argv)
        enable.start()

class ExtensionApp(Application):
    '''CLI for extension management.'''
    name = u'jupyter_dashboards_bundlers extension'
    description = u'Utilities for managing the jupyter_dashboards_bundlers extension'
    examples = ""

    subcommands = {}
    
    if _new_extensions:
        subcommands.update({
            "quick-setup": (
                ExtensionQuickSetupApp,
                "Install and enable everything in the package"
            ),
            "quick-remove": (
                ExtensionQuickRemovalApp,
                "Disable and uninstall everything in the package"
            )
        })
    else:
        subcommands.update(dict(
            activate=(
                ExtensionActivateApp,
                "Activate the extension."
            ),
            deactivate=(
                ExtensionDeactivateApp,
                "Deactivate the extension."
            )
        ))

    def _classes_default(self):
        classes = super(ExtensionApp, self)._classes_default()

        # include all the apps that have configurable options
        for appname, (app, help) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

    @catch_config_error
    def initialize(self, argv=None):
        super(ExtensionApp, self).initialize(argv)

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            self.print_help()
            sys.exit(1)

        # This starts subapps
        super(ExtensionApp, self).start()

def main():
    ExtensionApp.launch_instance()
