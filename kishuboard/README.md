# Install from pypi

To install the extension from pypi, execute:

```bash
pip install kishuboard
```

To remove the extension, execute:

```bash
pip uninstall kishuboard
```
# Install from source code:
Note: You will need NodeJS to build the kishuboard, please make sure you have node on your computer, or install it from [here](https://nodejs.org/en/download/).
1. enter the directory of the current file
2. build the NodeJS frontend
```bash
npm init # If you are building it from the source code for the first time
npm run build
```
3. [optional] Install kishu core from source code
```bash
source ../.env/bin/activate # activate the virtual environment
pip install ../kishu # install kishu from source code
pip install -r requirements.txt #install other dependencies
```
4. install kishu board
```bash
pip install .
```
5. run the kishuboard
```bash
kishuboard
```
And then you should be able to  visit the kishuboard at localhost://5000.

## test in dev mode
1. enter the directory of this readme file
2. start the kishuboard server(backend) in dev mode
```bash
cd kishuboard
flask --app server run
```
3. start the kishuboard frontend in dev mode
```bash
cd .. # go back to the directory of this readme file
npm start
```
And you should be able to visit the kishuboard at **localhost://3000**.
## Releasing
To build a new release of kishuboard, please refer to [RELEASE.md](./RELEASE.md)