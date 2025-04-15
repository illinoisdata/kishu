# KishuBoard: Interactive GUI for Kishu
Kishuboard is a dashboard extension of Kishu. With the interactive GUI provided by KishuBoard, you can browse, compare and search commits, checkout code/kernel variables to previous commits, branch out exploration, etc., in a straightforward and intuitive way. This [video](https://youtu.be/2RnUnlYUVLc) gives an overview of Kishuboard's features.

Kishuboard is part of our broader vision to support version control for computational notebooks. It builds on our HCI research of building intuitive interfaces for interactive data science workflows. See our papers here for more details:
- [Enhancing Computational Notebooks with Code+Data Space Versioning.](https://arxiv.org/abs/2504.01367)
- [Large-scale Evaluation of Notebook Checkpointing with AI Agents](https://arxiv.org/abs/2504.01377)
## Getting Started
### pypi installation
To install the extension from pypi, execute:

```bash
pip install kishuboard
```

### launch Kishuboard
And then, launch it with:
```bash
kishuboard
```
Now you should be able to visit it at ``localhost://4999``.

When Kishu is attached to a new notebook, **refresh** the notebook list. To enter the GUI of a specific notebook, simply click on its entry in the list.

<img width="400" src="../docs/images/kishuboard_menu.png"/>

## Features of Kishuboard
This [video](https://youtu.be/2RnUnlYUVLc) gives an overview of Kishuboard's features. Kishuboard enables these commonly used features:

1. **Automatic Commit.**
Each time a cell is executed, Kishu automatically creates a commit. Kishuboard displays detailed commit information, such as the executed code and associated variables.

2. **Select and Checkout.**
Restore both the code and variables to a selected point in the history.

3. **Select and Rollback.**
Revert only the variables to a previous state while keeping the current notebook code intact.

4. **Search Commits.**
Locate specific commits by filtering with commit messages, tags, or variable names that were modified.

5. **Track Variable History.**
Enter a variable name into the search bar to highlight all commits that have changed its value for one-by-one inspection.

6. **Diff Between Commits.**
Hold ``Ctrl``(or ``commmand`` for mac) to select any two commits and view the differences between them.

7. **Metadata Management.**
Edit commit metadata such as branch names, commit messages, and tags.

## Contributing

### Install from Source Code and Dev mode deployment:
Kishuboard depends on NodeJS. Install it [here](https://nodejs.org/en/download/).

1. Install Kishu into your virtual environment first by following the instructions [here](README.md).
2. Enter the directory of the current README.md file
3. Build the NodeJS frontend
```bash
npm init # Run only if you are building it from the source code for the first time
npm install # Run only if you are building it from the source code for the first time
```
4. Install Kishuboard flask backend
```bash
pip install -e .
```
5. Launch Kishuboard in dev mode
```
npm start
```
Once Kishuboard is launched, you should be able to visit it at **localhost://3000**. Refresh the page in your browser to update the display after changing frontend code.