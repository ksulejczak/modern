requirements/test.txt: requirements/test.in
	pip-compile --upgrade $^ --output-file=$@


install: requirements/test.txt
	pip install -r $<
