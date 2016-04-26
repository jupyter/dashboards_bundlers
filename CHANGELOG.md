# Changelog

## 0.5.0 (2016-04-26)

* Add support for report layout in Thebe-based deployments
* Add bundler to download a zip for deployment on `jupyter-incubator/dashboards_server`
* Improve documentation about bundling associated assets
* Make compatible with Jupyter Notebook 4.0.x to 4.2.x

## 0.4.0 (2016-03-04)

* Fix authorization header format for deployment to dashboard server
* Support bundling of frontend assets when deploying to dashboard server
* Make forward compatible with `declarative widgets>=0.5.0`

## 0.3.1 (2016-02-23)

* Fix compatibility with `jupyter_dashboards>=0.4.2` (internal lodash path change)

## 0.3.0 (2016-02-13)

* Add bundler to deploy to `jupyter-incubator/dashboards_server`

## 0.2.2 (2016-02-07)

* Fix compatibility with latest nbconvert (`jupyter nbconvert`)

## 0.2.1 (2016-01-26)

* Hide stderr and Thebe errors in dashboard UI

## 0.2.0 (2016-01-21)

* Separate `pip install` from `jupyter dashboards [install | activate | deactivate]`
* Fix local deploy when base URL is set on Jupyter Notebook server

## 0.1.1 (2015-12-30)

* Fix missing static assets in release

## 0.1.0 (2015-12-30)

* First release with local dashboard and PHP app options
