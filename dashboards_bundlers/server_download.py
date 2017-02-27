# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import shutil
import tempfile
from .server_upload import make_upload_bundle


def bundle(handler, model):
    '''
    Downloads a notebook, either by itself, or within a zip file with
    associated data and widget files, for manual deployment to a Jupyter
    Dashboard Server.
    '''
    # Noteook implementation passes ContentManager models. This bundler
    # only works with local files anyway.
    abs_nb_path = os.path.join(
        handler.settings['contents_manager'].root_dir,
        model['path']
    )

    # Get name of notebook from filename
    notebook_basename = os.path.basename(abs_nb_path)
    notebook_name = os.path.splitext(notebook_basename)[0]

    # Python 2/3 compatible try/finally to cleanup a temp working directory
    tmp_dir = tempfile.mkdtemp()
    try:
        output_dir = os.path.join(tmp_dir, notebook_name)
        # Reuse the same logic we would use to send a zip file or notebook
        # file to a dashboard server, but send it back to the web browser
        # not to another server
        bundle_path = make_upload_bundle(abs_nb_path, output_dir, handler.tools)

        if bundle_path == abs_nb_path:
            # Send the notebook alone: it has no associated resources
            handler.set_header('Content-Disposition',
                               'attachment; filename="%s"' % notebook_basename)
            handler.set_header('Content-Type', 'application/json')
        else:
            # Send a zip of the notebook and its associated resources
            handler.set_header('Content-Disposition',
                               'attachment; filename="%s"' % (notebook_name + '.zip'))
            handler.set_header('Content-Type', 'application/zip')

        with open(bundle_path, 'rb') as bundle_file:
            handler.write(bundle_file.read())
        handler.finish()

    finally:
        # We read and send synchronously, so we can clean up safely after finish
        shutil.rmtree(tmp_dir, True)
