import nbformat

if __name__ == '__main__':
    from coverage.coverage_test_cases import LIB_COVERAGE_TEST_CASES

    for test_case in LIB_COVERAGE_TEST_CASES:
        nb = nbformat.v4.new_notebook()
        nb.cells.append(nbformat.v4.new_code_cell(source="\n".join(test_case.import_statements)))
        nb.cells.append(nbformat.v4.new_code_cell(source="\n".join(test_case.var_declare_statements)))
        nb.cells.append(nbformat.v4.new_code_cell(source="\n".join(test_case.var_modify_statements)))
        with open(f"coverage/coverage_notebooks/{test_case.class_name}.ipynb", mode="w", encoding="utf-8") as f:
            nbformat.write(nb, f)
