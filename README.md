[![PyPI version](https://badge.fury.io/py/jupyter_dashboards_bundler.svg)](https://badge.fury.io/py/jupyter_dashboards) [![Google Group](https://img.shields.io/badge/-Google%20Group-lightgrey.svg)](https://groups.google.com/forum/#!forum/jupyter)

# Jupyter Dashboards Bundlers

Collection of reference implementation bundlers that convert, package, and deploy notebooks as standalone dashboards.

NOTE: This package provides *Deploy As* / *Download As* options in Jupyter Notebook that are currently redudant with the ones provided by the latest stable *jupyter_dashboards* release. We are in the process of extracting the bundlers out of that extension and will remove this note when they reside here and here alone. See [jupyter-incubator/dashboards#151](https://github.com/jupyter-incubator/dashboards/issues/151) for details.

## What It Gives You

* *File &rarr; Deploy as &rarr; Local dashboard* menu item to deploy the current notebook as a dashboard within the same Jupyter Notebook server instance.

## Prerequisites

* Jupyter Notebook 4.0.x running on Python 3.x or Python 2.7.x
* jupyter_cms>=0.3.0
* jupyter_dashboards>=0.3.0
* Edge Chrome, Firefox, or Safari

## Install It

`pip install jupyter_dashboards_bundlers`

Restart your Notebook server if you did not have `jupyter_cms` previously installed.

## Use It

Currently, there is only one bundler available in this package. It converts your notebook to a web application and deploys it to your Jupyter Notebook server for local use. To use it:

1. Write a notebook.
2. Define a dashboard layout using the `jupyter_dashboards` extension.
3. Click *File &rarr; Deploy as &rarr; Local dashboard*.
4. Enjoy your dashboard after the redirect.
