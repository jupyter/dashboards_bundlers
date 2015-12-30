# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

.PHONY: build clean dev help install sdist test install

# Version of Python to dev/test against
PYTHON?=python3
# CMS package to use for dev, expressed as a pip installable
CMS_PACKAGE?=jupyter_cms
# Dashboards package to use for dev, expressed as a pip installable
DASHBOARDS_PACKAGE?=jupyter_dashboards

# Using pyspark notebook to get both a python2 and python3 env
REPO:=jupyter/pyspark-notebook:a388c4a66fd4
DEV_REPO:=jupyter/pyspark-notebook-db-dev:a388c4a66fd4
PYTHON2_SETUP:=source activate python2

help:
	@echo 'Host commands:'
	@echo '     build - build dev image'
	@echo '     clean - clean built files'
	@echo '       dev - start notebook server in a container with source mounted'
	@echo '   install - install latest sdist into a container'
	@echo '     sdist - build a source distribution into dist/'
	@echo '      test - run unit tests within a container'

build:
	@-docker rm -f dev-build
	@docker run -it --user jovyan --name dev-build \
		$(REPO) bash -c 'pip install --no-binary :all: $(CMS_PACKAGE) $(DASHBOARDS_PACKAGE); \
			$(PYTHON2_SETUP); \
			pip install --no-binary :all: $(CMS_PACKAGE) $(DASHBOARDS_PACKAGE)'
	@docker commit dev-build $(DEV_REPO)
	@-docker rm -f dev-build

clean:
	@-rm -rf dist
	@-rm -rf *.egg-info
	@-rm -rf __pycache__ */__pycache__ */*/__pycache__
	@-find . -name '*.pyc' -exec rm -fv {} \;

dev: dev-$(PYTHON)

dev-python2: SETUP_CMD?=$(PYTHON2_SETUP); pushd /src && pip install --no-deps -e . && popd
dev-python2: _dev

dev-python3: SETUP_CMD?=pushd /src && pip install --no-deps -vvv -e . && popd
dev-python3: _dev

_dev: NB_HOME?=/root
_dev: CMD?=sh -c "python --version; jupyter notebook --no-browser --port 8888 --ip=0.0.0.0"
_dev: AUTORELOAD?=no
_dev:
	@docker run -it --rm \
		--user jovyan \
		-p 9500:8888 \
		-e AUTORELOAD=$(AUTORELOAD) \
		-v `pwd`:/src \
		$(DEV_REPO) bash -c '$(SETUP_CMD); $(CMD)'

install: CMD?=exit
install:
	@docker run -it --rm \
		--user jovyan \
		-v `pwd`:/src \
		$(REPO) bash -c 'cd /src/dist && \
			pip install --no-binary :all: $$(ls -1 *.tar.gz | tail -n 1) && \
			$(CMD)'

sdist: REPO?=jupyter/pyspark-notebook:$(TAG)
sdist:
	@docker run -it --rm \
		-v `pwd`:/src \
		$(REPO) bash -c 'cp -r /src /tmp/src && \
			cd /tmp/src && \
			python setup.py sdist $(POST_SDIST) && \
			cp -r dist /src'

test: test-$(PYTHON)

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
release: sdist
