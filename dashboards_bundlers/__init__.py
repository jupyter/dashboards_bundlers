# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.


def _jupyter_bundlerextension_paths():
    '''API for notebook bundler installation on notebook 5.0+'''
    return [{
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
