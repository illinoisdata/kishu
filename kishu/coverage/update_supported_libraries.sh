# Run from kishu directory

python -m pip install -r coverage/supported-libraries.txt
python coverage/run_tests.py
python coverage/update_coverage_doc.py --path ../docs/src/supported_libraries.rst