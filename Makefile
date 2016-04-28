# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

.PHONY: build clean dev help install sdist test install

# Version of Python to dev/test against
PYTHON?=python3
# CMS package to use for dev, expressed as a pip installable
CMS_PACKAGE?=jupyter_cms
# Dashboards package to use for dev, expressed as a pip installable
DASHBOARDS_PACKAGE?=jupyter_dashboards
# Decl widgets package to use for dev, expressed as a pip installabe
WIDGETS_PACKAGE?=jupyter_declarativewidgets

# Using pyspark notebook to get both a python2 and python3 env
REPO:=jupyter/pyspark-notebook:0017b56d93c9
DEV_REPO:=jupyter/pyspark-notebook-db-dev:0017b56d93c9
PYTHON2_SETUP:=source activate python2

define EXT_DEV_SETUP
	pushd /src && \
	pip install --no-deps -e . && \
	jupyter dashboards_bundlers activate && \
	popd
endef

define NOTEBOOK_SERVER
@docker run -it --rm \
	-p 9500:8888 \
	-e AUTORELOAD=$(AUTORELOAD) \
	-e DASHBOARD_SERVER_URL=$(DASHBOARD_SERVER_URL) \
	-e DASHBOARD_REDIRECT_URL=$(DASHBOARD_REDIRECT_URL) \
	-e DASHBOARD_SERVER_AUTH_TOKEN=$(DASHBOARD_SERVER_AUTH_TOKEN) \
	-v `pwd`:/src \
	-v `pwd`/etc/notebooks:/home/jovyan/work
endef

help:
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build the dev Docker image
	@-docker rm -f dev-build
	@docker run -it --name dev-build \
		$(REPO) bash -c 'pip install --no-binary :all: $(CMS_PACKAGE) $(DASHBOARDS_PACKAGE) $(WIDGETS_PACKAGE) && \
			jupyter cms install --user --symlink --overwrite && \
			jupyter dashboards install --user --symlink --overwrite && \
			jupyter cms activate && \
			jupyter dashboards activate'
	@docker commit dev-build $(DEV_REPO)
	@-docker rm -f dev-build
	@docker run -it --name dev-build \
		$(DEV_REPO) bash -c '$(PYTHON2_SETUP) && \
			pip install --no-binary :all: requests $(CMS_PACKAGE) $(DASHBOARDS_PACKAGE) $(WIDGETS_PACKAGE) && \
			jupyter cms install --user --symlink --overwrite && \
			jupyter dashboards install --user --symlink --overwrite && \
			jupyter cms activate && \
			jupyter dashboards activate'
	@docker commit dev-build $(DEV_REPO)
	@-docker rm -f dev-build

clean: ## Clean source tree
	@-rm -rf dist
	@-rm -rf *.egg-info
	@-rm -rf __pycache__ */__pycache__ */*/__pycache__
	@-find . -name '*.pyc' -exec rm -fv {} \;

dev: dev-$(PYTHON) ## Start notebook server in a container with source mounted

dev-python2: CMD?=start-notebook.sh
dev-python2:
	$(NOTEBOOK_SERVER) \
		$(DEV_REPO) bash -c '$(PYTHON2_SETUP) && python --version && $(EXT_DEV_SETUP) && $(CMD)'

dev-python3: CMD?=start-notebook.sh
dev-python3:
	$(NOTEBOOK_SERVER) \
		$(DEV_REPO) bash -c 'python --version && $(EXT_DEV_SETUP) && $(CMD)'

bash: ## Run a bash shell in the dev container
	$(NOTEBOOK_SERVER) $(DEV_REPO) bash -c '$(EXT_DEV_SETUP) && bash'

dev-with-decl-widgets: CMD?=start-notebook.sh
dev-with-decl-widgets: ## Same as dev but w/ declarative widgets (no bower)
	$(NOTEBOOK_SERVER) \
		$(DEV_REPO) bash -c 'pip install requests && \
			jupyter declarativewidgets install --user --symlink --overwrite && \
			jupyter declarativewidgets activate && \
		 	$(EXT_DEV_SETUP) && $(CMD)'

dev-with-dashboard-server: CMD?=start-notebook.sh
dev-with-dashboard-server: DASHBOARD_REDIRECT_URL?=$$(docker-machine ip $$(docker-machine active))
dev-with-dashboard-server: ## Same as dev but w/ decl widgets and Docker link to dashboards-server container
	$(NOTEBOOK_SERVER) \
		--link dashboard-server:dashboard-server \
		-e DASHBOARD_SERVER_URL=http://dashboard-server:3000 \
		-e DASHBOARD_REDIRECT_URL=http://$(DASHBOARD_REDIRECT_URL):3000 \
		$(DEV_REPO) bash -c 'pip install requests && \
			jupyter declarativewidgets install --user --symlink --overwrite && \
			jupyter declarativewidgets activate && \
		 	$(EXT_DEV_SETUP) && $(CMD)'

install: CMD?=exit
install: ## Install and activate the sdist package in the container
	@docker run -it --rm \
		--user jovyan \
		-v `pwd`:/src \
		$(REPO) bash -c 'cd /src/dist && \
			pip install --no-binary :all: $$(ls -1 *.tar.gz | tail -n 1) && \
			jupyter dashboards_bundlers activate && \
			$(CMD)'

sdist: ## Build a source distribution in dist/
	@docker run -it --rm \
		-v `pwd`:/src \
		$(REPO) bash -c 'cp -r /src /tmp/src && \
			cd /tmp/src && \
			python setup.py sdist $(POST_SDIST) && \
			cp -r dist /src'

test: test-$(PYTHON) ## Run tests

test-python2: SETUP_CMD?=$(PYTHON2_SETUP);
test-python2: _test

test-python3: _test

_test: CMD?=cd /src; python --version; python -B -m unittest discover -s test
_test:
# Need to use two commands here to allow for activation of multiple python versions
	@docker run -it --rm \
		-v `pwd`:/src \
		$(DEV_REPO) bash -c '$(SETUP_CMD) $(CMD)'

release: POST_SDIST=register upload
release: sdist ## Package and release to PyPI
