import csv
import enum
import pickle
from importlib.metadata import version
from pathlib import Path
from typing import Any, Dict, List, Tuple

from coverage.coverage_test_cases import LibCoverageTestCase
from kishu.planning.idgraph import IdGraph


class TestResult(str, enum.Enum):
    success = "success"
    fail = "fail"
    skip_nondeterministic = "skip_nondeterministic"
    nondeterministic_false_positive = "nondeterministic_false_positive"
    bad_test_case = "bad_test_case"
    id_graph_error = "id_graph_error"


class LibCoverageTesting:
    def __init__(self) -> None:
        self.test_results_list: List[List] = []

    def run_lib_coverage_tests(self, lib_coverage_test_cases: List[LibCoverageTestCase]) -> None:
        """
        Runs the library coverage tests with the test cases.
        """
        for test_case in LIB_COVERAGE_TEST_CASES:
            result, err = self._run_lib_coverage_test(test_case)
            self._add_test_results_to_list(test_case, result, err)

    def _run_lib_coverage_test(self, test_case: LibCoverageTestCase) -> Tuple[TestResult, str]:
        # Init empty libraries as environment for exec.
        globals: Dict[str, Any] = {}
        locals: Dict[str, Any] = {}

        # Import libraries for testing the object.
        for stmt in test_case.import_statements:
            exec(stmt, globals, locals)

        # Declare the object.
        for stmt in test_case.var_declare_statements:
            exec(stmt, globals, locals)

        # Pickle dump the original object. Don't do anything if it fails.
        var_before_pickle = None
        try:
            var_before_pickle = pickle.dumps(locals[test_case.var_name])
        except Exception:
            pass

        # Pickle dump the original object again. Don't do anything if it fails.
        var_before_pickle_2 = None
        try:
            var_before_pickle_2 = pickle.dumps(locals[test_case.var_name])
        except Exception:
            pass

        # Generate 2 ID graphs for the original object.
        try:
            idgraph_original = IdGraph.from_object(locals[test_case.var_name])
        except Exception as e:
            return TestResult.id_graph_error, str(e)

        try:
            idgraph_original_2 = IdGraph.from_object(locals[test_case.var_name])
        except Exception as e:
            return TestResult.id_graph_error, str(e)

        # If both ID graph generation and pickle dump are non-deterministic, skip test case.
        # If only ID graph generation is non-deterministic, the test case is a false positive.
        if idgraph_original != idgraph_original_2:
            if var_before_pickle != var_before_pickle_2:
                return TestResult.skip_nondeterministic, ""
            else:
                return TestResult.nondeterministic_false_positive, ""

        # If the ID graphs are equal but the pickle dumps are not, the test case is bad.
        if var_before_pickle != var_before_pickle_2:
            return TestResult.bad_test_case, ""

        # Modify the object.
        for stmt in test_case.var_modify_statements:
            exec(stmt, globals, locals)

        # Generate an ID graph for the modified object.
        try:
            idgraph_modified = IdGraph.from_object(locals[test_case.var_name])
        except Exception as e:
            return TestResult.id_graph_error, str(e)

        # Pickle dump the modified object. Don't do anything if it fails.
        var_after_pickle = None
        try:
            var_after_pickle = pickle.dumps(locals[test_case.var_name])
        except Exception:
            pass

        # If pickled values are equal, the test case is bad as the modification doesn't
        # modify the object.
        if var_before_pickle == var_after_pickle:
            return TestResult.bad_test_case, ""

        # Success if ID graphs before and after modifying the object are different
        if idgraph_original != idgraph_modified:
            return TestResult.success, ""
        else:
            return TestResult.fail, ""

    def _add_test_results_to_list(self, test_case: LibCoverageTestCase, result: TestResult, error: str = "") -> None:
        """
        Record test results.

        @param obj: tested object.
        @param result: test result.
        @param error: error string if any.
        """
        # Get the module name and version from the class name.
        module_version = version(test_case.module_name)

        self.test_results_list.append([test_case.module_name, module_version, test_case.class_name, result, error])

    def write_test_results(self, test_results_location: Path) -> None:
        """
        Write test results to a provided CSV file.
        """
        Path.mkdir(test_results_location.parents[0], exist_ok=True)
        with open(test_results_location, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.test_results_list)


if __name__ == "__main__":
    from coverage.coverage_test_cases import LIB_COVERAGE_TEST_CASES

    lib_coverage_testing = LibCoverageTesting()
    lib_coverage_testing.run_lib_coverage_tests(LIB_COVERAGE_TEST_CASES)
    lib_coverage_testing.write_test_results(Path(__file__).resolve().parents[1] / "build" / "lib_coverage_test_results.csv")
