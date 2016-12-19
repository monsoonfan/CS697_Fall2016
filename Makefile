run:
	rm -f Solution*.csv
	/cygdrive/c/Python35/python genetic_scheduler.py
	cp Solution*.csv ViewerCode/solution.csv
	cd ViewerCode && /cygdrive/c/Python35/python matrix_viewer.py 069 MWF && /cygdrive/c/Python35/python matrix_viewer.py 069 TR

convert.%:
	cp $* ViewerCode/solution.csv
	cd ViewerCode && /cygdrive/c/Python35/python matrix_viewer.py 069 MWF && /cygdrive/c/Python35/python matrix_viewer.py 069 TR
