import argparse
import csv
import os
from pathlib import Path

from coverage.run_tests import TestResult

PAGE_TEMPLATE = """
Supported Libraries
=====


This is the current list of libraries, their versions, and their classes supported by Kishu:

- ✅ supported: All changes to instances of this class are always captured.

- ❓ unstable: Kishu may report changes on non-changes to instances of this class, i.e., false positives.

- ❌ failing: Some changes to an instance of this class may not be captured.

.. code-block:: console

"""


def write_supported_libraries_page(supported_libraries_page_path: Path):
    test_results = list(csv.reader(open(Path(__file__).resolve().parent / os.pardir / "build/lib_coverage_test_results.csv")))

    # Split results into successes and failures
    successes = [result for result in test_results if result[3] == TestResult.success.name]
    unstables = [
        result
        for result in test_results
        if result[3] in {TestResult.skip_nondeterministic.name, TestResult.nondeterministic_false_positive.name}
    ]
    failures = [result for result in test_results if result[3] in {TestResult.fail.name, TestResult.id_graph_error.name}]

    # Sort results by alphabetical order of module.
    successes.sort()
    failures.sort()

    # Write .rst file.
    newline = "\n"
    with open(supported_libraries_page_path, "w") as supported_librares_page:
        supported_librares_page.write(
            f"{PAGE_TEMPLATE}"
            f"{newline.join(f'    ✅ {result[0]}=={result[1]}, {result[2]}' for result in successes)}{newline}"
            f"{newline.join(f'    ❓ {result[0]}=={result[1]}, {result[2]}' for result in unstables)}{newline}"
            f"{newline.join(f'    ❌ {result[0]}=={result[1]}, {result[2]}' for result in failures)}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-P", "--path", help="Path of supported libraries page")
    args = parser.parse_args()
    write_supported_libraries_page(args.path)
