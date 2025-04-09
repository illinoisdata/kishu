# KishuBoard
This is a dashboard extension of Kishu. With the interactive GUI provided by KishuBoard, you can browse, compare and search commits, checkout code/kernel variables to previous commits; branch out exploration etc. in a straightforward and intuitive way. This [video](https://youtu.be/2RnUnlYUVLc) gives an overview of Kishuboard's features.

Kishuboard is part of our broader vision to support version control for computational notebooks. It builds on our HCI research of building intuitive interface for interactive data science workflow. Kishuboard was introduced in these papers:
- [Enhancing Computational Notebooks with Code+Data Space Versioning.](https://arxiv.org/abs/2504.01367)
- [Large-scale Evaluation of Notebook Checkpointing with AI Agents](https://arxiv.org/abs/2504.01377)
## Getting Started
### pypi installation
To install the extension from pypi, execute:

```bash
pip install kishuboard
```

### launch Kishuboard
```bash
kishuboard
```
And then you should be able to visit kishuboard at localhost://4999. 

When Kishu is attached to a new notebook, **refresh** the notebook list. To enter the GUI of a specific notebook, simply click on its entry in the list.

<img width="400" src="../docs/images/kishuboard_menu.png"/>

## Features of Kishuboard
This [video](https://youtu.be/2RnUnlYUVLc) gives an overview of Kishuboard's features. Kishuboard enables seamless one-click access to the following features (but is not limited to them):

1. Automatic Commit
Each time a cell is executed, Kishu automatically creates a commit. Kishuboard displays detailed commit information, including the executed code and associated variables.

2. Select and Checkout
Restore both the code and variables to a selected point in the history with a single click.

3. Select and Rollback
Revert only the variables to a previous state while keeping the current notebook code intact.

4. Search Commits
Quickly locate specific commits by filtering with commit messages, tags, or variable names that were modified.

5. Track Variable History
Enter a variable name into the search bar to highlight all commits that have changed its value, allowing you to inspect them one by one.

6. Diff Between Commits
Hold Ctrl to select any two commits and view the differences between them.

7. Metadata Management
Edit commit metadata such as branch names, commit messages, and tags effortlessly.

## Contributing

### Install from Source Code and Dev mode deployment:
Note: You will need NodeJS to build the kishuboard, please make sure you have it on your computer, or install it from [here](https://nodejs.org/en/download/).

1. If you haven't, install Kishu into your virtual environment first by following the instructions [here](README.md)
2. enter the directory of the current README.md file
3. build the NodeJS frontend
```bash
npm init # Run only if you are building it from the source code for the first time
npm install # Run only if you are building it from the source code for the first time
```
4. install Kishuboard flask backend
```bash
pip install -e .
```
5. Launch Kishuboard in dev mode
```
npm start
```
And you should be able to visit kishuboard at **localhost://3000**. Refresh the page in your browser to update the frontend after changing frontend code.