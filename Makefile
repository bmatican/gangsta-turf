.PHONY: clean python-deps

clean:
	find -name "*.pyc" -exec rm -v {} +

python-deps:
	pip install -r requirements/common.txt
