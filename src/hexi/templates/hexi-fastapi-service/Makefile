.PHONY: run test hexi-doctor hexi-run

run:
	uvicorn app.main:app --reload

test:
	python -m pytest -q

hexi-doctor:
	hexi doctor

hexi-run:
	@if [ -z "$(TASK)" ]; then echo "Usage: make hexi-run TASK=\"...\""; exit 1; fi
	hexi run "$(TASK)"
