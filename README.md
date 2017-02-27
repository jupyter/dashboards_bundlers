[![PyPI version](https://badge.fury.io/py/jupyter_dashboards_bundlers.svg)](https://badge.fury.io/py/jupyter_dashboards_bundlers) [![Google Group](https://img.shields.io/badge/-Google%20Group-lightgrey.svg)](https://groups.google.com/forum/#!forum/jupyter)

# Jupyter Dashboards Bundlers

The dashbaords bundler extension is an add-on for Jupyter Notebook. It takes a
notebook with layout information from the [dashboard layout
extention](https://github.com/jupyter/dashboards) and lets you download it or
directly publish it to the experimental [dashboard
server](https://github.com/jupyter-incubator/dashboards_server).

![Dashboard bundlers screenshot](etc/bundlers_intro.png)

## What It Gives You

* *File &rarr; Download as &rarr; Jupyter Dashboards Server bundle (.zip)* - menu item to download the current notebook and its associated assets for manual deployment on a [Jupyter Dashboards](https://github.com/jupyter-incubator/dashboards_server) server.
* *File &rarr; Deploy as &rarr; Dashboard on Jupyter Dashboards Server* - menu item to deploy the current notebook and its associated assets as a dashboard on a target [Jupyter Dashboards](https://github.com/jupyter-incubator/dashboards_server) server.

## Prerequisites

* Jupyter Notebook >=5.0 running on Python 3.x or Python 2.7.x
* Edge, Chrome, Firefox, or Safari

If you are running an older version of the notebook server, you should use a
version of this package prior to the 0.9 release.

## Installing and Enabling

The following steps install the extension package using `pip` and enable the
extension in the active Python environment.

```bash
pip install jupyter_dashboards_bundlers
jupyter bundlerextension enable --sys-prefix --py dashboards_bundlers
```

## Disabling and Uninstalling

The following steps deactivate the extension in the active Python environment
and uninstall the package using `pip`.

```bash
jupyter bundlerextension disable --sys-prefix --py dashboards_bundlers
pip uninstall jupyter_dashboards_bundlers
```

## Use It

Currently, there are two bundlers available in this package.

### Download as &rarr; Jupyter Dashboards Server bundle (.zip)

The first option bundles your notebook and any associated frontend assets into
a zip file which you can manually deploy on a [Jupyter Dashboards
Server](https://github.com/jupyter-incubator/dashboards_server). To use it:

1. Write a notebook.
2. Define a dashboard layout using the `jupyter_dashboards` extension.
3. If the notebook requires any frontend assets (e.g., CSS files), [associate
   them with the
   notebook](etc/notebooks/associations_demo/associations_demo.ipynb).
4. Click *File &rarr; Download as &rarr; Jupyter Dashboards Server bundle
   (.zip)*.
5. Install
   [jupyter-incubator/dashboards_server](https://github.com/jupyter-incubator/dashboards_server)
   by following the project README.
5. Unzip the bundle in the `data/` directory of the Jupyter Dashboard Server
   and run it.

This bundler is compatible with:

* `jupyter_declarativewidgets>=0.5.0` when deploying dashboards with declarative widgets
* `ipywidgets>=5.0.0,<6.0.0` when deploying dashboards with ipywidgets

### Deploy as &rarr; Dashboard on Jupyter Dashboards Server

The second option directly sends your notebook and any associated frontend
assets to a [Jupyter Dashboards
Server](https://github.com/jupyter-incubator/dashboards_server). To use it:

0. Run an instance of the Jupyter Dashboards Server by following the
   instructions in the
   [jupyter-incubator/dashboards_server](https://github.com/jupyter-incubator/dashboards_server)
   project README.
1. Set the following environment variables before launching your Jupyter
   Notebook server with the bundler extensions installed.
    * `DASHBOARD_SERVER_URL` - protocol, hostname, and port of the dashboard
      server to which to send dashboard notebooks
    * `DASHBOARD_REDIRECT_URL` (optional) - protocol, hostname, and port to use
      when redirecting the user's browser after upload if different from
      `DASHBOARD_SERVER_URL` and if upload response has no link property from
      the dashboard server (v0.6.0+)
    * `DASHBOARD_SERVER_AUTH_TOKEN` (optional) - upload token required by the
      dashboard server
    * `DASHBOARD_SERVER_NO_SSL_VERIFY` (optional) - skip verification of the
      dashboard server SSL certificate (for use in dev / trusted environments
      only!)
2. Write a notebook.
3. Define a dashboard layout using the `jupyter_dashboards` extension.
4. If the notebook requires any frontend assets (e.g., CSS files), [associate
   them with the
   notebook](etc/notebooks/associations_demo/associations_demo.ipynb).
5. Click *File &rarr; Deploy as &rarr; Dashboard on Jupyter Dashboard Server*.
6. Enjoy your dashboard after the redirect.

This bundler is compatible with:

* `jupyter_declarativewidgets>=0.5.0` when deploying dashboards with declarative widgets
* `ipywidgets>=5.0.0,<6.0.0` when deploying dashboards with ipywidgets

## Caveats

It is important to realize that kernels launched by your deployed dashboard
will not being running in the same directory or possibly even the same
environment as your original notebook. You must refer to external, kernel-side
resources in a portable manner (e.g., put it in an external data store). You
must also ensure your kernel environment has all the same
libraries installed as your notebook authoring environment.

It is also your responsibility to associate any frontend, dashboard-side assets
with your notebook before packaging it for deployment. To aid in this task, the
two bundlers here take advantage of the notebook association feature supported
by the notebook bundler API. See the [associations
demo](etc/notebooks/associations_demo/associations_demo.ipynb) for the markup
you can use to refer to external files that should be included in your
dashboard deployment.

If you are using [declarative
widgets](https://github.com/jupyter-incubator/declarativewidgets) in your
dashboard, you should be mindful of the following when you deploy your
dashboard:

* You must run the entire notebook successfully before deploying. This action
  ensures all external Polymer components are properly installed on the
  notebook server and can be bundled with your converted notebook.
