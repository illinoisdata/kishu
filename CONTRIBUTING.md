# Contributing to Kishu

Welcome and thank you for contributing to Kishu!

## Development

We recommend creating a virtual environment (e.g., `python -m venv .venv`) before starting developing Kishu.

Please refer to individual modules' README.md for development notes on how to install in development mode, format, lint, test, etc.

- [Kishu](kishu/README.md)
- [Kishu's JupyterLab extension](jupyterlab_kishu/README.md)
- [Kishuboard](kishuboard/README.md)

For a quick installation of all modules in development mode:

```bash
(cd kishu && make install)
(cd jupyterlab_kishu && make install)
(cd kishuboard && make install)
```

### Releasing Modules

Follow these steps to release module(s):

1. Create a branch for releasing module(s).
2. Increment version number(s) in respective configuration file(s) for each target module. See (Semantic Versioning)[https://semver.org] for a guideline on incrementing the version number.
3. Commit the change.
4. Create a pull request at the [repository](https://github.com/illinoisdata/kishu/pulls).
5. Apply respective label(s) `release-*` to the pull request (e.g., `release-kishu` for `kishu` module).
6. After the pull request is approved, merge the pull request.

After the pull request is merged, `Release` GitHub Action will automatically detect the label(s) and release module(s) accordingly.
