.requirements.out: requirements.txt
	pip install -r $< | tee $@

clean.requirements.out:
	rm -f .requirements.out
