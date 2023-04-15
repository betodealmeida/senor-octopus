pyenv: .python-version

.python-version: requirements/test.txt
	if [ -z "`pyenv virtualenvs | grep srocto`" ]; then\
	    pyenv virtualenv srocto;\
	fi
	if [ ! -f .python-version ]; then\
	    pyenv local srocto;\
	fi
	pip install -r requirements/test.txt
	touch .python-version

test: pyenv
	pytest --cov=src/senor_octopus -vv tests/ --doctest-modules src/senor_octopus

clean:
	pyenv virtualenv-delete srocto

spellcheck:
	codespell -S "*.json" src/senor_octopus docs/*rst tests templates *.rst

check:
	pre-commit run --all-files
