# Run from kishu directory

python -m pip install -r coverage/supported-libraries.txt
python -m coverage.run_tests
python -m coverage.update_coverage_doc --path ../docs/src/supported_libraries.rst
