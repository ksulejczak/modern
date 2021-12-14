requirements/dev.txt: requirements/dev.in
	pip-compile --upgrade $^ --output-file=$@

requirements/test.txt: requirements/test.in
	pip-compile --upgrade $^ --output-file=$@

install: requirements/dev.txt requirements/test.txt
	for f in $^; do pip install -r $$f; done
