# KishuBoard
This is a dash-board extension of Kishu. With the interactive GUI provided by KishuBoard, you can browse, compare and search commits, checkout code/kernel variables to previous commits; branch out etc in a straightforward way.
## Getting Started
### pypi installation
To install the extension from pypi, execute:

```bash
pip install kishuboard
```
To remove the extension, execute:

```bash
pip uninstall kishuboard
```
### starting up via kishuboard
```bash
kishuboard
```
And then you should be able to  visit the kishuboard at localhost://4999.

### Install from source code:
Note: You will need NodeJS to build the kishuboard, please make sure you have node on your computer, or install it from [here](https://nodejs.org/en/download/).
1. enter the directory of the current file
2. build the NodeJS frontend
```bash
npm init # If you are building it from the source code for the first time
npm install # If you are building it from the source code for the first time
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
And then you should be able to  visit the kishuboard at localhost://4999.

## Development
### Dev mode deployment
To run the kishuboard in dev mode, you will need to start the kishuboard server and the kishuboard frontend separately.
1. enter the directory of this readme file
2. start the kishuboard server(backend) in dev mode
```bash
source ../.env/bin/activate # activate the virtual environment
cd kishuboard
python server.py
```
3. start the kishuboard frontend in dev mode
```bash
cd .. # go back to the directory of this readme file
npm init # If you are building it from the source code for the first time
npm install # If you are building it from the source code for the first time
npm start
```
And you should be able to visit the kishuboard at **localhost://3000**. Refresh the page in your browser to update the frontend after changing frontend code.
To build a new release of kishuboard, please refer to [RELEASE.md](./RELEASE.md)