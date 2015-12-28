# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import shutil
import tempfile
from os.path import join as pjoin
from ..local_deploy import bundle_file_references, bundle_web_static, \
    bundle_declarative_widgets, bundle_index

# Location of this file
HERE = os.path.abspath(os.path.dirname(__file__))
# Absolute path to the default template
DEFAULT_TEMPLATE_PATH = pjoin(HERE, 'jinja_templates', 'index.php.tpl')

# Starting simply, keep all assets here in Python
DOCKERFILE_TMPL = '''\
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

FROM php:5.6-apache
ENV KERNEL_SERVICE_URL {kernel_service_url}
ENV TMPNB_MODE {tmpnb_mode}
COPY . /var/www/html/
'''

MANIFEST_TMPL = '''\
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
---
applications:
- name: {notebook_name}
  memory: 128M
  env:
    KERNEL_SERVICE_URL: {kernel_service_url}
    TMPNB_MODE: "{tmpnb_mode}"
'''

README_TMPL = '''\
This zip file bundles the dashboard web application with manifests for running
as a Docker container and deploying to a Cloud Foundry PaaS such as IBM Bluemix.

## First, a note on stability and security

The dashboard web application requires a kernel provisioner API such as tmpnb or
Jupyter Notebook itself. It then uses Thebe to communicate with this kernel 
service. Deploying a kernel service, properly configuring a dashboard to talk to
it, securing access, ensuring availability of all assets required for proper 
code execution, etc. are all very much works in progress. See 
https://github.com/jupyter-incubator/dashboards#deploy for the current
state of affairs.

Treat this code as proof of concept. Do not use it in production settings. Take
care to avoid privacy violations and exposing other data accessible to the 
kernel service.

## Configurating the dashboard

The dashboard contains copies of code cells that need to be executed. A pair of
environment variables determine where the execution kernels come from, as well
as the API used to control them:

* `KERNEL_SERVICE_URL` - the Jupyter server that the dashboard will leverage
* `TMPNB_MODE` - boolean for whether the kernel service is a multi-user tmpnb
                 setup (`true`), rather than a single Jupyter notebook server
                 (`false`)

## Running in a Docker Container

The provided Dockerfile can be used to run the dashboard application as-is. Doing
so will serve the application on port 9500 of the Docker host. The Dockerfile
specifies `KERNEL_SERVICE_URL` and TMPNB_MODE values for the notebook server that
generated this zip file bundle. When changed, the container should be killed and
rerun.

## Running in a Cloud Foundry PaaS

The accompanying manifest.yml file specifies the
`KERNEL_SERVICE_URL` and `TMPNB_MODE` values for the notebook server that
generated this zip file bundle. If being pushed using the `cf` CLI, the zip file
must be unpacked and its contents pushed from the filesystem. As of this writing,
 `cf` will not make use of a manifest within a zip file when pushing that zip
file. If modified in the manifest.yml, the app must be pushed again. If modified
using `cf set-env`, the app must be restaged using `cf restage <appname>` to update
its environment.
'''

def bundle(handler, abs_nb_path):
    '''
    Bundles a notebook as a PHP dashboard application and downloads it as a 
    zip file for deployment elsewhere.
    '''
    # Get name of notebook from filename
    notebook_basename = os.path.basename(abs_nb_path)
    notebook_name = os.path.splitext(notebook_basename)[0]

    # Python 2/3 compatible try/finally to cleanup a temp working directory
    tmp_dir = tempfile.mkdtemp()
    try:
        output_dir = pjoin(tmp_dir, notebook_name)
        os.makedirs(output_dir)

        # Generate the index.html file
        bundle_index(output_dir, abs_nb_path, DEFAULT_TEMPLATE_PATH, 'index.php')

        # Include frontend files referenced via the jupyter_cms bundle mechanism
        bundle_file_references(output_dir, abs_nb_path, handler.tools)

        # Include static web assets (e.g., Thebe)
        bundle_web_static(output_dir)

        # Copy declarative widgets if they were used
        bundle_declarative_widgets(output_dir, abs_nb_path)

        # Bundle the supporting files used for deployment
        bundle_meta(output_dir, notebook_name, handler)

        # zip it up
        shutil.make_archive(output_dir, 'zip', output_dir)

        # Set response headers for zip
        zip_filename = os.path.splitext(notebook_name)[0] + '.zip'
        handler.set_header('Content-Disposition',
                           'attachment; filename="%s"' % zip_filename)
        handler.set_header('Content-Type', 'application/zip')

        # Send zip
        with open(output_dir + '.zip', 'rb') as zipfile:
            handler.write(zipfile.read())

        handler.finish()
    finally:
        # Always clean up the working directory
        shutil.rmtree(tmp_dir, True)

def bundle_meta(output_dir, notebook_name, handler):
    '''
    Add a README.md, Dockerfile, and manifest.yml to the output directory. Try
    to set reasonable defaults for the TMPNB_MODE and KERNEL_SERVICE_URL
    based on values in the environment of this notebook server.
    '''
    # See if notebook environment has a flag about the tmpnb mode
    tmpnb_mode = os.getenv('TMPNB_MODE', 'false')

    # Determine what server to use for later execution of the dashboard
    kernel_service_url = os.getenv('KERNEL_SERVICE_URL')
    if kernel_service_url is None:
        # Use this jupyter notebook server as the default kernel server if
        # one is not explicitly named
        kernel_service_url = '{proto}://{host}{path}'.format(
            proto=handler.request.protocol,
            host=handler.request.host,
            path=handler.settings['base_url']
        )
        tmpnb_mode = 'false'

    with open(pjoin(output_dir, 'Dockerfile'), 'w') as fh:
        fh.write(DOCKERFILE_TMPL.format(
            kernel_service_url=kernel_service_url,
            tmpnb_mode=tmpnb_mode
        ))

    with open(pjoin(output_dir, 'manifest.yml'), 'w') as fh:
        fh.write(MANIFEST_TMPL.format(
            kernel_service_url=kernel_service_url,
            tmpnb_mode=tmpnb_mode,
            notebook_name=notebook_name
        ))

    with open(pjoin(output_dir, 'README.md'), 'w') as fh:
        fh.write(README_TMPL)
