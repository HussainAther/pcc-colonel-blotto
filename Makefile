.PHONY: test probe preflight

test:
	python -m pytest -q

probe:
	python -m pcc_colonel_blotto mechanism-probe --output-dir validation

preflight: test probe
