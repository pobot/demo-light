PYTHON=`which python`
NAME=`python setup.py --name`

dist: source deb

source:
	$(PYTHON) setup.py sdist

deb:
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

test:
	unit2 discover -s tests -t .
	python -mpytest weasyprint

check:
	find . -name \*.py | grep -v "^test_" | xargs pylint --errors-only --reports=n

clean:
	$(PYTHON) setup.py clean
	rm -rf build/ MANIFEST dist/ deb_dist/ $(NAME).egg-info
	find . -name '*.pyc' -delete
	
