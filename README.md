[![PyPI version](https://badge.fury.io/py/jupyter_dashboards_bundlers.svg)](https://badge.fury.io/py/jupyter_dashboards_bundlers) [![Google Group](https://img.shields.io/badge/-Google%20Group-lightgrey.svg)](https://groups.google.com/forum/#!forum/jupyter)

# Jupyter Dashboards Bundlers

Collection of reference implementation bundlers that convert, package, and deploy notebooks as standalone dashboards.

## What It Gives You

* *File &rarr; Deploy as &rarr; Local dashboard* menu item to deploy the current notebook as a dashboard within the same Jupyter Notebook server instance.
* *File &rarr; Download as &rarr; PHP Dashboard bundle (.zip)* menu item to download the current notebook as a PHP dashboard web frontend that you can deploy and configure to use your own kernel provider (e.g., tmpnb + kernel gateway).

## Prerequisites

* Jupyter Notebook 4.0.x running on Python 3.x or Python 2.7.x
* `jupyter_cms>=0.3.0`
* `jupyter_dashboards>=0.3.0`
* Edge, Chrome, Firefox, or Safari

## Install It

```bash
# install the python package
pip install jupyter_dashboards_bundlers
# enable the extension in your ~/.jupyter config
jupyter dashboards_bundlers activate
```

## Uninstall It

```bash
jupyter dashboards_bundlers deactivate
pip uninstall dashboards_bundlers
```

## Use It

Currently, there are two bundlers available in this package. The first converts your notebook to a dashboard web application and deploys it to your Jupyter Notebook server for local use. To use it:

1. Write a notebook.
2. Define a dashboard layout using the `jupyter_dashboards` extension.
3. Click *File &rarr; Deploy as &rarr; Local Dashboard*.
4. Enjoy your dashboard after the redirect.

The second converts your notebook to a dashboard web application and zips it up with a Dockerfile and Cloud Foundry manifest. To use it:

1. Write a notebook.
2. Define a dashboard layout using the `jupyter_dashboards` extension.
3. Click *File &rarr; Download as &rarr; PHP Dashboard bundle (.zip)*.
4. Unzip the download.
5. Refer to the `README.md` in the unzipped folder for deployment requirements.

## Caveats

See https://github.com/jupyter-incubator/dashboards#deploy for a full rundown on the current status of dashboard deployment.

It is important to realize that kernels launched by your deployed dashboard will not being running in the same directory or possibly even the same environment as your original notebook. You must refer to external, kernel-side resources in a portable manner (e.g., put it in an external data store, use absolute file paths if your only concern is *File &rarr; Deploy as &rarr; Local Dashboard*). You must also ensure your kernel environment has all the same libraries installed as your notebook authoring environment.

It is also your responsibility to associate any frontend, dashboard-side assets with your notebook before packaging it for deployment. To aid in this task, the bundlers here take advatnage of the notebook association feature provided by the `jupyter_cms` package. See the [associations demo](https://github.com/jupyter-incubator/contentmanagement/) for the markup you can use to refer to external files that should be included in your dashboard deployment.

If you are using [declarative widgets](https://github.com/jupyter-incubator/declarativewidgets) in your dashboard, you should be mindful of the following when you deploy your dashboard.

* You must run the entire notebook successfully before deploying. This action ensures all external Polymer components are properly installed on the notebook server and can be bundled with your converted notebook.
* You cannot use `<urth-core-import>` elements in custom Polymer widgets that you develop outside your notebook. See [dashboards issue #78](https://github.com/jupyter-incubator/dashboards/issues/78) for the discussion and current workaround.
