for FILE in `cat test_notebooks.txt`
do
	for inc in True False
	do
        echo $FILE
		python3 tests/helpers/criu_runner.py -N $FILE -C 10 -I $inc
		wait
	done
done
python3 tests/experiments/script.py
wait
