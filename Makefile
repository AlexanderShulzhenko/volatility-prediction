.PHONY: format
format:
	pre-commit run --all-files

.PHONY: lint
lint:
	python -m pylint ./src/ --ignore=__main__.py --rcfile .pylintrc
