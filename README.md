[![build status](https://github.com/illinoisdata/kishu/actions/workflows/kishu.yml/badge.svg)](htps://github.com/illinoisdata/kishu)
[![codecov](https://codecov.io/gh/illinoisdata/kishu/graph/badge.svg?token=14WRVYQBZO)](https://codecov.io/gh/illinoisdata/kishu)
[![Python version](https://img.shields.io/pypi/pyversions/kishu)](https://pypi.org/project/kishu/)
[![PyPi version](https://img.shields.io/pypi/v/kishu)](https://pypi.org/project/kishu/)
<!---
[![commits last month](https://img.shields.io/github/commit-activity/m/illinoisdata/ElasticNotebook)](htps://github.com/illinoisdata/kishu)
[![GitHub stars](https://img.shields.io/github/stars/illinoisdata/ElasticNotebook)](htps://github.com/illinoisdata/kishu)
--->

# Kishu: Versioned and Undoable Notebook System

Kishu is a system for intelligent versioning of notebook session states on Jupyter-based platforms (e.g. JupyterLab, Jupyter Hub). Kishu efficiently creates checkpoints of both the variable and code states of a notebook session, allowing users to both undo cell executions and manage branching states containing objects such as machine learning models, plots, and dataframes through a Git-like commit and checkout interface.

## Using Kishu

Kishu can be installed from [PyPI](https://pypi.org/project/kishu/):

```bash
pip install kishu jupyterlab_kishu
```

Once installed, you are ready to use Kishu in your notebook workflows for undoing cell executions and managing branching notebook states.

### Initializing Kishu
**Initialize Kishu to your notebook**: To start protecting your notebook session, Kishu can be initialized and attached through the `Kishu > Initialize/Re-attach` option under the `Kishu` tab (left) or in the Jupyter command palette (right). Alternatively, you can use the shortcut `Ctrl+K then Ctrl+I` / `⌘+K then ⌘+I`.

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="473" alt="init_dropdown" src="https://github.com/user-attachments/assets/12a8beb7-2414-48e8-ad8d-c092308d444c" />
<img width="348" alt="init_palette" src="https://github.com/user-attachments/assets/a53d55d7-a187-40d4-926f-49cea20360d4" />

<br> <!-- HTML tag to force a line break if you want more space -->

You will see the below notification if Kishu is initialized successfully:

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="313" alt="init_success" src="https://github.com/user-attachments/assets/654c7cdc-07a6-4741-aa1b-49f8f9272418" />

<br> <!-- HTML tag to force a line break if you want more space -->

### Undoable Notebook Workflow
**Automatic Tracking**: Once initialized, Kishu will start automatically saving the variable state after each cell execution.
**Undoing a cell execution:** To undo your latest cell execution, you can use the `Kishu > Initialize/Re-attach` option under the `Kishu` tab (left) or in the Jupyter command palette (right). Alternatively, you can use the shortcut `Ctrl+K then Ctrl+Z` / `⌘+K then ⌘+Z`.

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="468" alt="undo_dropdown" src="https://github.com/user-attachments/assets/87f4b76d-dba6-45ba-852f-b5f441f312ff" />
<img width="288" alt="undo_palette" src="https://github.com/user-attachments/assets/51c7b71e-9fdf-4f50-b659-e7ca10982dd8" />

<br> <!-- HTML tag to force a line break if you want more space -->

If successful, you will see the following notification, and your variable state will be rolled back to that before your latest cell execution. 

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="314" alt="undo_success" src="https://github.com/user-attachments/assets/90669b80-7baa-40e8-910b-c205df0e4ebc" />

<br> <!-- HTML tag to force a line break if you want more space -->

**Only affects variable state:** Undoing cell executions **only affects the variable state** (right). The code state (i.e., the cells you write, left) is untouched. This can be useful, for example, to 'un-drop' a dataframe column dropped by a cell while keeping the cell code itself intact:

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="600" alt="flow1_2" src="https://github.com/user-attachments/assets/869ee070-9d94-4163-a317-332ac85f4a30"/>

<br> <!-- HTML tag to force a line break if you want more space -->

### Branching Notebook Workflow

Kishu can also be used to manage branching code and variable states; it supports making **checkpoints** of the notebook and variable state at any point during a notebook session, which can be returned to later via a **checkout**.

**Committing to make a checkpoint:** Kishu can store the current state of your notebook, including both the variable state and your code state, with the `Kishu > Commit` option under the `Kishu` tab (left) or in the Jupyter command palette (right). Alternatively, you can use the shortcut `Ctrl+K then Ctrl+C` / `⌘+K then ⌘+C`.  

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="466" alt="commit_dropdown" src="https://github.com/user-attachments/assets/87c40f88-1c0e-4624-b41e-0102c4e52a12" />
<img width="288" alt="commit_palette" src="https://github.com/user-attachments/assets/6a7cc869-2189-4ce2-bb7e-e0f11e12d867" />

<br> <!-- HTML tag to force a line break if you want more space -->

You will be then prompted to enter a **commit message**. Use something memorable so you can easily return to this commit later:

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="297" alt="commit_message" src="https://github.com/user-attachments/assets/cac8b890-8455-4690-9b10-df24b7afc726" />

<br> <!-- HTML tag to force a line break if you want more space -->

You will see the below message if the commit is successful:

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="314" alt="commit_success" src="https://github.com/user-attachments/assets/cd996fd8-a350-4954-91f8-cd423d4b25d4" />

<br> <!-- HTML tag to force a line break if you want more space -->

**Checkout to a checkpoint:** You can return to any session state that has been committed in the past with the `Kishu > Checkout` option under the `Kishu` tab (left) or in the Jupyter command palette (right). Alternatively, you can use the shortcut `Ctrl+K then Ctrl+V` / `⌘+K then ⌘+V`.  

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="288" alt="checkout_dropdown" src="https://github.com/user-attachments/assets/0377cea1-0171-416c-8f55-d6fc1af721ad" />
<img width="469" alt="checkout_palette" src="https://github.com/user-attachments/assets/cfa6616a-1a6c-444d-b141-6297c6c48ba5" />

<br> <!-- HTML tag to force a line break if you want more space -->

This will bring up a menu for you to select the appropriate checkpoint:

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="716" alt="Screenshot 2024-12-19 at 14 33 47" src="https://github.com/user-attachments/assets/3cc1c604-f222-462a-afab-e9b2efe01222" />

<br> <!-- HTML tag to force a line break if you want more space -->

You will see the below message if the checkout is successful:

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="314" alt="Screenshot 2024-12-19 at 14 35 30" src="https://github.com/user-attachments/assets/dee886c9-1e13-469d-8563-966cea8da7be" />

<br> <!-- HTML tag to force a line break if you want more space -->

Checking out will replace both the current variable and code state with that of the selected checkpoint (see below). It will also **overwrite your current variable and code state**; commit to make a checkpoint before checking out if you wish to keep your current notebook state.

<br> <!-- HTML tag to force a line break if you want more space -->

<img width="600" alt="checkout_workflow" src="https://github.com/user-attachments/assets/a6e0796c-fe88-43ac-82df-6db645652b15"/>

<br> <!-- HTML tag to force a line break if you want more space -->

## Configuring Kishu

Kishu can be configured through editing the `~/.kishu/config.ini` file. A full list of configurable options can be found [here](docs/src/usage.rst).

## Supported Libraries

This is the current list of libraries, their versions, and their classes supported by Kishu:
```
- ✅ : supported: All changes to instances of this class are always captured.
- ❓ : unstable: Kishu may report changes on non-changes to instances of this class, i.e., false positives.
- ❌ : failing: Some changes to an instance of this class may not be captured.

    ✅ arrow==1.3.0, arrow.arrow.Arrow
    ✅ astropy==5.2.2, astropy.convolution.Box2DKernel
    ✅ astropy==5.2.2, astropy.convolution.Gaussian2DKernel
    ✅ astropy==5.2.2, astropy.io.fits.HDUList
    ✅ astropy==5.2.2, astropy.io.fits.PrimaryHDU
    ✅ astropy==5.2.2, astropy.modeling.fitting.LinearLSQFitter
    ✅ astropy==5.2.2, astropy.modeling.functional_models.Ellipse2D
    ✅ astropy==5.2.2, astropy.modeling.functional_models.Linear1D
    ✅ astropy==5.2.2, astropy.modeling.polynomial.Polynomial1D
    ✅ astropy==5.2.2, astropy.modeling.polynomial.Polynomial2D
    ✅ astropy==5.2.2, astropy.nddata.NDData
    ✅ astropy==5.2.2, astropy.nddata.NDDataRef
    ✅ astropy==5.2.2, astropy.stats.SigmaClip
    ✅ astropy==5.2.2, astropy.table.QTable
    ✅ astropy==5.2.2, astropy.units.Quantity
    ✅ astropy==5.2.2, astropy.visualization.PercentileInterval
    ✅ astropy==5.2.2, astropy.wcs.WCS
    ✅ bokeh==2.4.3, bokeh.plotting._figure.figure
    ✅ catboost==1.2.3, catboost
    ✅ dask==2023.5.0, dask
    ✅ dataprep==0.4.5, dataprep.datasets
    ✅ dataprep==0.4.5, dataprep.eda.intermediate.Intermediate
    ✅ dill==0.3.8, dill
    ✅ gensim==4.3.2, gensim
    ✅ gym==0.26.2, gym
    ✅ ipywidgets==7.8.5, ipywidgets
    ✅ keras==2.13.1, keras.src.initializers.initializers.RandomNormal
    ✅ keras==2.13.1, keras.src.initializers.initializers.RandomUniform
    ✅ keras==2.13.1, keras.src.layers.core.dense.Dense
    ✅ keras==2.13.1, keras.src.optimizers.schedules.learning_rate_schedule.ExponentialDecay
    ✅ lightgbm==4.3.0, lightgbm.basic.Dataset
    ✅ llm==0.13.1, llm.default_plugins.openai_models.Chat
    ✅ lmfit==1.2.2, lmfit.parameter.Parameters
    ✅ matplotlib==3.7.5, matplotlib.colors.ListedColormap
    ✅ matplotlib==3.7.5, matplotlib.dates.AutoDateFormatter
    ✅ matplotlib==3.7.5, matplotlib.dates.WeekdayLocator
    ✅ matplotlib==3.7.5, matplotlib.ticker.AutoLocator
    ✅ networkx==3.1, networkx.classes.digraph.DiGraph
    ✅ networkx==3.1, networkx.classes.graph.Graph
    ✅ nltk==3.8.1, nltk.stem.porter.PorterStemmer
    ✅ numpy==1.24.3, ast
    ✅ numpy==1.24.3, copy
    ✅ numpy==1.24.3, datetime.time
    ✅ numpy==1.24.3, datetime.timedelta
    ✅ numpy==1.24.3, hashlib
    ✅ numpy==1.24.3, itertools
    ✅ numpy==1.24.3, json
    ✅ numpy==1.24.3, numpy.ndarray
    ✅ numpy==1.24.3, numpy.ndarray
    ✅ numpy==1.24.3, pickle
    ✅ numpy==1.24.3, random.Random
    ✅ numpy==1.24.3, re.Pattern
    ✅ numpy==1.24.3, urllib.request.Request
    ✅ numpy==1.24.3, uuid.UUID
    ✅ opencv-python==4.9.0.80, cv2
    ✅ optuna==3.5.0, optuna.Study
    ✅ pandas==1.5.3, pandas.DataFrame
    ✅ pandas==1.5.3, pandas.Series
    ✅ pathlib==1.0.1, pathlib.PosixPath
    ✅ photoutils==0.0.1, photutils.psf.matching.CosineBellWindow
    ✅ photoutils==0.0.1, photutils.psf.matching.HanningWindow
    ✅ photoutils==0.0.1, photutils.utils.CutoutImage
    ✅ photoutils==0.0.1, photutils.utils.ImageDepth
    ✅ plotly==5.18.0, plotly.express
    ✅ plotly==5.18.0, plotly.figure_factory
    ✅ plotly==5.18.0, plotly.graph_objects
    ✅ plotly==5.18.0, plotly.graph_objs
    ✅ plotly==5.18.0, plotly.io
    ✅ plotly==5.18.0, plotly.offline
    ✅ plotly==5.18.0, plotly.subplots
    ✅ polars==0.14.29, polars.DataFrame
    ✅ prophet==1.1.5, prophet.Prophet
    ✅ pyspark==3.5.1, pyspark.sql
    ✅ qiskit==0.45.0, qiskit.QuantumCircuit
    ✅ scikit-image==0.21.0, skimage
    ✅ scikit-image==0.21.0, skimage.morphology
    ✅ scikit-learn==1.3.2, sklearn.cluster
    ✅ scikit-learn==1.3.2, sklearn.cluster
    ✅ scikit-learn==1.3.2, sklearn.compose
    ✅ scikit-learn==1.3.2, sklearn.datasets
    ✅ scikit-learn==1.3.2, sklearn.datasets
    ✅ scikit-learn==1.3.2, sklearn.decomposition
    ✅ scikit-learn==1.3.2, sklearn.discriminant_analysis
    ✅ scikit-learn==1.3.2, sklearn.dummy
    ✅ scikit-learn==1.3.2, sklearn.ensemble
    ✅ scikit-learn==1.3.2, sklearn.feature_extraction.text
    ✅ scikit-learn==1.3.2, sklearn.feature_selection
    ✅ scikit-learn==1.3.2, sklearn.impute
    ✅ scikit-learn==1.3.2, sklearn.impute
    ✅ scikit-learn==1.3.2, sklearn.impute
    ✅ scikit-learn==1.3.2, sklearn.kernel_ridge
    ✅ scikit-learn==1.3.2, sklearn.linear_model
    ✅ scikit-learn==1.3.2, sklearn.linear_model
    ✅ scikit-learn==1.3.2, sklearn.manifold
    ✅ scikit-learn==1.3.2, sklearn.metrics
    ✅ scikit-learn==1.3.2, sklearn.metrics.pairwise
    ✅ scikit-learn==1.3.2, sklearn.mixture
    ✅ scikit-learn==1.3.2, sklearn.model_selection
    ✅ scikit-learn==1.3.2, sklearn.multiclass
    ✅ scikit-learn==1.3.2, sklearn.naive_bayes
    ✅ scikit-learn==1.3.2, sklearn.neighbors
    ✅ scikit-learn==1.3.2, sklearn.neural_network
    ✅ scikit-learn==1.3.2, sklearn.pipeline
    ✅ scikit-learn==1.3.2, sklearn.preprocessing
    ✅ scikit-learn==1.3.2, sklearn.random_projection
    ✅ scikit-learn==1.3.2, sklearn.svm
    ✅ scikit-learn==1.3.2, sklearn.tree
    ✅ scikit-learn==1.3.2, sklearn.utils
    ✅ scipy==1.10.1, scipy.interpolate
    ✅ scipy==1.10.1, scipy.ndimage
    ✅ scipy==1.10.1, scipy.ndimage.interpolate
    ✅ scipy==1.10.1, scipy.optimize
    ✅ scipy==1.10.1, scipy.signal
    ✅ scipy==1.10.1, scipy.signal.windows
    ✅ scipy==1.10.1, scipy.sparse
    ✅ scipy==1.10.1, scipy.spatial
    ✅ scipy==1.10.1, scipy.spatial
    ✅ scipy==1.10.1, scipy.spatial.distance
    ✅ scipy==1.10.1, scipy.spatial.distance._hausdorff
    ✅ scipy==1.10.1, scipy.special
    ✅ scipy==1.10.1, scipy.stats
    ✅ statsmodels==0.14.1, statsmodels.api
    ✅ tensorflow==2.13.1, tensorflow
    ✅ tensorflow==2.13.1, tensorflow.keras.models
    ✅ tensorflow==2.13.1, tensorflow.keras.optimizers
    ✅ textblob==0.17.1, textblob.TextBlob
    ✅ torch==2.4.1, torch
    ✅ torch==2.4.1, torch.nn
    ✅ torch==2.4.1, torch.nn.functional
    ✅ torch==2.4.1, torch.utils.data
    ✅ transformers==4.38.2, huggingface
    ✅ transformers==4.38.2, transformers
    ✅ typing==3.7.4.3, typing
    ✅ wordcloud==1.9.3, wordcloud.WordCloud
    ❓ matplotlib==3.7.5, matplotlib.Axes
    ❓ matplotlib==3.7.5, matplotlib.Axes
    ❓ seaborn==0.13.0, seaborn
    ❓ torch==2.4.1, torch.optim
    ❓ polars==0.14.29, polars.LazyFrame
    ❓ matplotlib==3.7.5, matplotlib.colors.BoundaryNorm
    ❓ matplotlib==3.7.5, matplotlib.lines.Line2D
    ❓ matplotlib==3.7.5, matplotlib.patches.Ellipse
    ❓ matplotlib==3.7.5, matplotlib.patches.Arrow
    ❓ matplotlib==3.7.5, matplotlib.image.AxesImage
    ❓ matplotlib==3.7.5, matplotlib.image.FigureImage
    ❓ matplotlib==3.7.5, matplotlib.offsetbox.AnchoredOffsetbox
    ❓ astropy==5.2.2, astropy.visualization.mpl_normalize.ImageNormalize
    ❓ astropy==5.2.2, astropy.wcs.Celprm
    ❓ matplotlib==3.7.5, 'mpl_toolkits.mplot3d.art3d.Line3DCollection
```

## Migrating Checkpoints

Kishu's per-notebook checkpoint files are stored under the `~/.kishu/` directory. For example, Kishu will store the checkpoint files for notebook with name `Untitled` under `~/.kishu/Untitled`. These checkpoints can be copied, along with the notebook, to a new machine where Kishu (and other libraries identical to the source environment) is installed for elastic migration.

## Limitations
Kishu may fail to correctly checkpoint notebook sessions containing the following items:

### Silent Pickling Errors

Kishu relies on the assumption that any object, when pickled then unpickled, is identical to the original object, and does not automatically detect cases where this assumption is violated (i.e., silent pickling errors). This is typically caused by errors in the object class' [__reduce__](https://docs.python.org/3/library/pickle.html) function which acts as its pickling instructions; for example, an object with the below reduction (incorrectly) returns an empty (byte)string when pickled.

```python
  def \_\_reduce\_\_(self):
      return ""
```

As a potential workaround, you can add object classes with incorrect reductions to a [blocklist](docs/src/usage.rst) in Kishu's config to inform it to never try to store (and always recompute) objects belonging to these classes.

### Non-Deterministic and Unpicklable Objects
Kishu relies on cell replay to reconstruct unpicklable objects (e.g., generators). However, if the unpicklable object itself is created through non-deterministic means, Kishu will fail to exactly recreate it on undo/checkout, for example (assuming the seed for `random` was not set):

```python
  nondet_gen = (i for i in range(random.randint(5, 10)))
```

## Learn More

Kishu's efficiency is enabled by its low-overhead session state monitoring, deduplicated variable storage, and optimized recomputation-assisted checkout. Our papers on Kishu can be found here; don't forget to star our repository and cite our papers if you like our work!

- [Kishu: Time-Traveling for Computational Notebooks](https://arxiv.org/abs/2406.13856)
- [ElasticNotebook: Enabling Live Migration for Computational Notebooks](https://arxiv.org/abs/2309.11083)
- [Transactional Python for Durable Machine Learning: Vision, Challenges, and Feasibility](https://dl.acm.org/doi/abs/10.1145/3595360.3595855)
- [Demonstration of ElasticNotebook: Migrating Live Computational Notebook States](https://dl.acm.org/doi/abs/10.1145/3626246.3654752)
