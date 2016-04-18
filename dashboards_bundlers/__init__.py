# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

def _jupyter_bundler_paths():
    '''API for notebook bundler installation on notebook 4.2'''
    return [{
            'name': 'dashboards_local_deploy',
            'label': 'Local Dashboard',
            'module_name': 'dashboards_bundlers.local_deploy',
            'group': 'deploy'
        },
        {
            'name': 'dashboards_php_download',
            'label': 'PHP Dashboard bundle (.zip)',
            'module_name': 'dashboards_bundlers.php_download',
            'group': 'download'
        },
        {
            'name': 'dashboards_server_upload',
            'label': 'Dashboard on Jupyter Dashboards Server',
            'module_name': 'dashboards_bundlers.server_upload',
            'group': 'deploy'
        },
        {
            'name': 'dashboards_server_download',
            'label': 'Jupyter Dashboards Server bundle (.zip)',
            'module_name': 'dashboards_bundlers.server_download',
            'group': 'download'
        }]
