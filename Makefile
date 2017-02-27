# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

.PHONY: activate build clean env help notebook nuke release sdist test

SA:=source activate
ENV:=dashboards-bundlers

help:
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

activate: ## eval $(make activate)
	@echo "$(SA) $(ENV)"

clean: ## Make a clean source tree
	@-rm -rf dist
	@-rm -rf *.egg-info
	@-rm -rf __pycache__ */__pycache__ */*/__pycache__
	@-find . -name '*.pyc' -exec rm -fv {} \;

build: env
env: ## Make a dev environment
	@conda create -y -n $(ENV) -c conda-forge python=3 \
		--file requirements.txt \
# Need to force notebook prerelease until 5.0 is out
	@$(SA) $(ENV) && \
		pip install --pre notebook && \
		pip install -e . && \
		jupyter bundlerextension enable --sys-prefix --py dashboards_bundlers

notebook: ## Make a notebook server
	$(SA) $(ENV) && jupyter notebook --notebook-dir=./etc/notebooks

nuke: clean ## Make clean + remove conda env
	-conda env remove -n $(ENV) -y

release: sdist ## Make a release on PyPI
	$(SA) $(ENV) && python setup.py sdist register upload

sdist: ## Make a dist/*.tar.gz source distribution
	$(SA) $(ENV) && python setup.py sdist

test: ## Make a test run
	$(SA) $(ENV) && python -B -m unittest discover -s test
