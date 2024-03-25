# Use twine for pypi upload (https://twine.readthedocs.io/en/stable/)
# First, build frontend
npm run build

# Second, build the distribution
python -m build

# Only authenticated users can run this command successfully
twine upload dist/*
