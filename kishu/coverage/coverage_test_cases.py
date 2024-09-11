from dataclasses import dataclass
from typing import List


@dataclass
class LibCoverageTestCase:
    """
        @param module_name: Name of the library which the object is from.
        @param class_name: Name of the class of the object.
        @param var_name: The name of the variable used for testing.
        @param import_statements: The import statements for the library.
        @param var_declare_statements: statements that declare the object.
        @param var_modify_statements: statements that alters the object
    """
    module_name: str
    class_name: str
    import_statements: List[str]
    var_name: str
    var_declare_statements: List[str]
    var_modify_statements: List[str]


LIB_COVERAGE_TEST_CASES: List[LibCoverageTestCase] = [
    LibCoverageTestCase(
        module_name="numpy",
        class_name="numpy.ndarray",
        var_name="a",
        import_statements=["import numpy as np"],
        var_declare_statements=["a = np.arange(6)"],
        var_modify_statements=["a[3] = 10"]
    ),
    LibCoverageTestCase(
        module_name="pandas",
        class_name="pandas.Series",
        var_name="a",
        import_statements=["import pandas as pd"],
        var_declare_statements=["a = pd.Series([1, 2, 3, 4])"],
        var_modify_statements=["a[2] = 0"]
    ),
    LibCoverageTestCase(
        module_name="pandas",
        class_name="pandas.DataFrame",
        var_name="a",
        import_statements=["import seaborn as sns"],
        var_declare_statements=["a = sns.load_dataset('penguins')"],
        var_modify_statements=["a.at[0, 'species'] = 'Changed'"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.Axes",
        var_name="a",
        import_statements=["import seaborn as sns"],
        var_declare_statements=[
            "df=sns.load_dataset('penguins')",
            "a = sns.scatterplot(data=df, x='flipper_length_mm', y='bill_length_mm')",
        ],
        var_modify_statements=["a.set_xlabel('Flipper Length')"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.Axes",
        var_name="a",
        import_statements=["import seaborn as sns"],
        var_declare_statements=[
            "df=sns.load_dataset('penguins')",
            "a = sns.scatterplot(data=df, x='flipper_length_mm', y='bill_length_mm')",
        ],
        var_modify_statements=["a.set_xlabel('Flipper Length')"]
    ),
    LibCoverageTestCase(
        module_name="qiskit",
        class_name="qiskit.QuantumCircuit",
        var_name="qc",
        import_statements=["import numpy as np", "from qiskit import QuantumCircuit"],
        var_declare_statements=[
            "qc = QuantumCircuit(3)"
        ],
        var_modify_statements=["qc.p(np.pi/2, 0)"]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="pickle",
        var_name="data",
        import_statements=["import pickle"],
        var_declare_statements=[
            "data = {'a': [1, 2.0, 3+4j], 'b': ('character string', b'byte string'), 'c': {None, True, False}}",
            "with open('data.pickle', 'wb') as f: pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)",
            "data['a'].append(4)"
        ],
        var_modify_statements=["with open('data.pickle', 'rb') as f: data = pickle.load(f)"]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="json",
        var_name="res",
        import_statements=["import json"],
        var_declare_statements=[
            "data = {'a': [1, 2.0]}",
            "res = json.dumps(data)"
        ],
        var_modify_statements=[ 
            "data['a'].append(4)",
            "res = json.dumps(data)"
        ]
    ),
    LibCoverageTestCase(
        module_name = "numpy",
        class_name = "itertools",
        var_name = "data",
        import_statements=["from itertools import accumulate", "import operator"],
        var_declare_statements=[
            "data = [3, 4, 6, 2, 1, 9]"
        ],
        var_modify_statements=[
            "data = list(accumulate(data, operator.mul))"
        ]
    ),
    LibCoverageTestCase(
        module_name = "ipywidgets",
        class_name = "ipywidgets",
        var_name = "w",
        import_statements=["import ipywidgets as widgets"],
        var_declare_statements=[
            "w = widgets.IntSlider()"
        ],
        var_modify_statements=[
            "w.value = 100"
        ]
    ),
    LibCoverageTestCase(
        module_name = "numpy",
        class_name = "hashlib",
        var_name = "res",
        import_statements=["import hashlib"],
        var_declare_statements=[
            "m = hashlib.sha256()",
            "m.update(b'Nobody inspects')",
            "res = m.digest()"
        ],
        var_modify_statements=[
            "m.update(b' the spammish repitition')",
            "res = m.digest()"
        ]
    ),
    LibCoverageTestCase(
        module_name="dill",
        class_name="dill",
        var_name="data",
        import_statements=["import dill as pickle"],
        var_declare_statements=[
            "data = {'a': [1, 2.0, 3+4j], 'b': ('character string', b'byte string'), 'c': {None, True, False}}",
            "with open('data.pickle', 'wb') as f: pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)",
            "data['d'] = lambda x: x**2"
        ],
        var_modify_statements=["with open('data.pickle', 'rb') as f: data = pickle.load(f)"]
    ),
    LibCoverageTestCase(
        module_name="dask",
        class_name="dask",
        var_name="x",
        import_statements=["import dask.array as da"],
        var_declare_statements=[
            "x = da.random.random((10000, 10000), chunks = (1000, 1000))",
        ],
        var_modify_statements=[
            "x = x + x.T"
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="copy",
        var_name="res",
        import_statements=["import copy"],
        var_declare_statements=[
            "x = [1, 2, 3]",
            "res = copy.copy(x)",
            "res = copy.deepcopy(res)"
        ],
        var_modify_statements=[
            "res = x.append(4)"
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="ast",
        var_name="node",
        import_statements=["import ast"],
        var_declare_statements=[
            "node = ast.UnaryOp()",
        ],
        var_modify_statements=[
            "node.op = ast.USub()",
            "node.operand = ast.Constant()",
            "node.operand.value = 5",
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="dataclasses",
        var_name="data",
        import_statements=["from dataclasses import dataclass"],
        var_declare_statements=[
            "class C: a: int",
            "DC = dataclass(C)",
            "data = DC(0)"
        ],
        var_modify_statements=["data.a = 1"]
    ),
    LibCoverageTestCase(
        module_name="typing",
        class_name="typing",
        var_name="list",
        import_statements=[
            "from typing import List"
        ],
        var_declare_statements=[
            "list: List[int] = [1, 2, 3]"
        ],
        var_modify_statements=[
            "list.append(4)"
        ]
    ),
    LibCoverageTestCase(
        module_name="wordcloud",
        class_name="wordcloud.WordCloud",
        var_name="wc",
        import_statements=[
            "import numpy as np",
            "from wordcloud import WordCloud"
        ],
        var_declare_statements=[
            "text = 'square'",
            "x, y = np.ogrid[:300, :300]",
            "mask = (x - 150) ** 2 + (y - 150) ** 2 > 130 ** 2",
            "mask = 255 * mask.astype(int)",
            "wc = WordCloud(background_color='white', repeat=True, mask=mask)",
            "wc.generate(text)"
        ],
        var_modify_statements=[
            "wc.generate('circle')"
        ]
    ),
    LibCoverageTestCase(
        module_name="textblob",
        class_name="textblob.TextBlob",
        var_name="blob",
        import_statements=[
            "from textblob import TextBlob"
        ],
        var_declare_statements=[
            "text = 'I havv a goood fone.'",
            "blob = TextBlob(text)",
        ],
        var_modify_statements=[
            "blob = blob.correct()"
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="uuid.UUID",
        var_name="uuid_obj",
        import_statements=["import uuid"],
        var_declare_statements=[
            "uuid_obj = uuid.uuid4()"
        ],
        var_modify_statements=[
            "uuid_obj = uuid_obj.hex[:8] + '0000-0000-0000-0000-' + uuid_obj.hex[20:]"
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="urllib.request.Request",
        var_name="req",
        import_statements=["import urllib.request"],
        var_declare_statements=[
            "url = 'https://www.example.com/'",
            "req = urllib.request.Request(url)"
        ],
        var_modify_statements=[
            "req.data = b'example data'"
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="datetime.timedelta",
        var_name="time_diff",
        import_statements=[
            "from datetime import timedelta"
        ],
        var_declare_statements=[
            "time_diff = timedelta(seconds=10)"
        ],
        var_modify_statements=[
            "dif2 = timedelta(minutes=5)",
            "time_diff = dif2 + time_diff"
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="datetime.time",
        var_name="current_time",
        import_statements=[
            "from datetime import time",
            "from datetime import timedelta",
            "from datetime import datetime"
        ],
        var_declare_statements=[
            "current_time = time(12, 0, 0)"
        ],
        var_modify_statements=[
            "delta = timedelta(hours=1, minutes=30)",
            "current_time = (datetime.combine(datetime.min, current_time) + delta).time()"
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="random.Random",
        var_name="rnd",
        import_statements=[
            "import random"
        ],
        var_declare_statements=[
            "rnd = random.Random()"
        ],
        var_modify_statements=[
            "rnd.seed(42)"
        ]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="re.Pattern",
        var_name="pattern",
        import_statements=[
            "import re"
        ],
        var_declare_statements=[
            r"pattern = re.compile(r'\b\w+\b')"
        ],
        var_modify_statements=[
            r"pattern = re.compile(r'\b[A-Z]+\b')"
        ]
    ),

    
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.cluster",
        var_name="kmeans",
        import_statements=["import numpy as np", "from sklearn.cluster import KMeans"],
        var_declare_statements=[
            "X = np.array([[1, 2], [1, 4], [1, 0], [10, 0], [10, 4], [10, 0]])",
            "kmeans = KMeans(n_clusters = 2, random_state = 0, n_init='auto').fit(X)"
        ],
        var_modify_statements=["kmeans.n_clusters=4"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.cluster",
        var_name="kmeans",
        import_statements=["import numpy as np", "from sklearn.cluster import MiniBatchKMeans"],
        var_declare_statements=[
            "X = np.array([[1, 2], [1, 4], [1, 0], [4, 2], [4, 0], [4, 4], [4, 5], [0, 1], [2, 2], [3, 2], [5, 5], [1, -1]])",
            "kmeans = MiniBatchKMeans(n_clusters = 2, random_state = 0, batch_size=6, n_init='auto')",
            "kmeans = kmeans.partial_fit(X[0:6,:])"
        ],
        var_modify_statements=["kmeans.batch_size=4"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.compose",
        var_name="ct",
        import_statements=[
            "import numpy as np",
            "from sklearn.compose import ColumnTransformer",
            "from sklearn.preprocessing import Normalizer"
        ],
        var_declare_statements=[
            "ct = ColumnTransformer([('norm1', Normalizer(norm='l1'), [0, 1]),('norm2', Normalizer(norm='l1'), slice(2, 4))])",
            "X = np.array([[0., 1., 2., 2.], [1., 1., 0., 1.]])",
            "ct.fit_transform(X)"
        ],
        var_modify_statements=[
            "ct.feature_names_in_ = ['feature1', 'feature2', 'feature3', 'feature4']"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.datasets",
        var_name="data",
        import_statements=["from sklearn.datasets import fetch_california_housing"],
        var_declare_statements=[
            "data = fetch_california_housing()"
        ],
        var_modify_statements=["data.data[0,0] = 15"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.datasets",
        var_name="X",
        import_statements=["from sklearn.datasets import make_friedman1"],
        var_declare_statements=[
            "X, y = make_friedman1(random_state=42)"
        ],
        var_modify_statements=["X[3,2] = 10"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.decomposition",
        var_name="transformer",
        import_statements=[
            "from sklearn.datasets import load_digits", 
            "from sklearn.decomposition import IncrementalPCA"
        ],
        var_declare_statements=[
            "X, _ = load_digits(return_X_y=True)",
            "transformer = IncrementalPCA(n_components=7, batch_size=200)"
        ],
        var_modify_statements=["transformer.batch_size = 201", "transformer.n_components=8"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.discriminant_analysis",
        var_name="clf",
        import_statements=[
            "import numpy as np",
            "from sklearn.discriminant_analysis import LinearDiscriminantAnalysis"
        ],
        var_declare_statements=[
            "X1 = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])",
            "X2 = np.array([[-1, 11], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])",
            "y = np.array([1, 1, 1, 2, 2, 2])",
            "clf = LinearDiscriminantAnalysis()",
            "clf.fit(X1, y)"
        ],
        var_modify_statements=["clf.fit(X2, y)"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.dummy",
        var_name="clf",
        import_statements=[
            "import numpy as np",
            "from sklearn.dummy import DummyClassifier"
        ],
        var_declare_statements=[
            "X = np.array([-1, 1, 1, 1])",
            "y = np.array([0, 1, 1, 1])",
            "clf = DummyClassifier(strategy='most_frequent')",
            "clf.fit(X, y)"
        ],
        var_modify_statements=["clf.n_classes_ = 11"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.ensemble",
        var_name="clf",
        import_statements=[
            "from sklearn.ensemble import AdaBoostClassifier",
            "from sklearn.datasets import make_classification"
        ],
        var_declare_statements=[
            "X, y = make_classification(n_samples=1000, n_features=4, n_informative=2, n_redundant=0, random_state=0, shuffle=False)",
            "X1, y1 = make_classification(n_samples=1000, n_features=4, n_informative=2, n_redundant=0, random_state=10, shuffle=False)",
            "clf = AdaBoostClassifier(n_estimators=100, algorithm='SAMME', random_state=42)",
            "clf.fit(X, y)"
        ],
        var_modify_statements=[
            "clf.n_estimators = 200",
            "clf.algorithm = 'SAMME.R'",
            "clf.random_state = 100"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.feature_extraction.text",
        var_name="vectorizer",
        import_statements=[
            "from sklearn.feature_extraction.text import CountVectorizer"
        ],
        var_declare_statements=[
            "corpus = ['This is the first document.','This document is the second document.','And this is the third one.','Is this the first document?']",
            "vectorizer = CountVectorizer()",
            "X = vectorizer.fit_transform(corpus)"
        ],
        var_modify_statements=[
            "vectorizer.stop_words_ = {'is', 'the', 'and'}"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.feature_selection",
        var_name="selector",
        import_statements=[
            "from sklearn.datasets import load_digits",
            "from sklearn.feature_selection import SelectPercentile, chi2"
        ],
        var_declare_statements=[
            "X, y = load_digits(return_X_y=True)",
            "selector = SelectPercentile(chi2, percentile=10).fit(X, y)",
            "X_new = selector.transform(X)"
        ],
        var_modify_statements=[
            "selector.pvalues_ = [0.1, 0.05, 0.2, 0.15]"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.impute",
        var_name="imp_mean",
        import_statements=[
            "import numpy as np",
            "from sklearn.impute import SimpleImputer"
        ],
        var_declare_statements=[
            "imp_mean = SimpleImputer(missing_values=np.nan, strategy='mean')",
            "imp_mean.fit([[7, 2, 3], [4, np.nan, 6], [10, 5, 9]])"
        ],
        var_modify_statements=["imp_mean.fit([[np.nan, 2, 3], [4, np.nan, 6], [10, 5, np.nan]])"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.impute",
        var_name="imputer",
        import_statements=[
            "import numpy as np",
            "from sklearn.impute import KNNImputer"
        ],
        var_declare_statements=[
            "X = [[7, 2, 3], [4, np.nan, 6], [10, 5, 9]]",
            "imputer = KNNImputer(n_neighbors=2)",
            "imputer.fit_transform(X)"
        ],
        var_modify_statements=["imputer.fit_transform([[np.nan, 2, 3], [4, np.nan, 6], [10, 5, np.nan]])"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.impute",
        var_name="imputer",
        import_statements=[
            "import numpy as np",
            "from sklearn.impute import KNNImputer"
        ],
        var_declare_statements=[
            "X = [[7, 2, 3], [4, np.nan, 6], [10, 5, 9]]",
            "imputer = KNNImputer(n_neighbors=2)",
            "imputer.fit_transform(X)"
        ],
        var_modify_statements=["imputer.fit_transform([[np.nan, 2, 3], [4, np.nan, 6], [10, 5, np.nan]])"]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.kernel_ridge",
        var_name="kernel_ridge",
        import_statements=[
            "import numpy as np",
            "from sklearn.kernel_ridge import KernelRidge"
        ],
        var_declare_statements=[
            "X = np.array([[1, 2], [3, 4], [5, 6]])",
            "y = np.array([1, 2, 3])",
            "kernel_ridge = KernelRidge(kernel='rbf', alpha=0.1)"
        ],
        var_modify_statements=[
            "kernel_ridge.fit(X, y)",
            "current_dual_coefficients = kernel_ridge.dual_coef_",
            "new_dual_coefficients = np.full_like(current_dual_coefficients, fill_value=0.5)",
            "kernel_ridge.dual_coef_ = new_dual_coefficients"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.linear_model",
        var_name="regression_model",
        import_statements=[
            "import numpy as np",
            "from sklearn.linear_model import LinearRegression"
        ],
        var_declare_statements=[
            "X = np.array([[1, 2], [3, 4], [5, 6]])",
            "y = np.array([1, 2, 3])",
            "regression_model = LinearRegression()",
            "regression_model.fit(X, y)",
        ],
        var_modify_statements=[
            "current_coefficients = regression_model.coef_",
            "new_coefficients = np.full_like(current_coefficients, fill_value=0.5)",
            "regression_model.coef_ = new_coefficients"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.linear_model",
        var_name="logistic_model",
        import_statements=[
            "import numpy as np",
            "from sklearn.linear_model import LogisticRegression"
        ],
        var_declare_statements=[
            "X = np.array([[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]])",
            "y = np.array([0, 0, 1, 1, 1])",
            "logistic_model = LogisticRegression()"
        ],
        var_modify_statements=[
            "logistic_model.fit(X, y)",
            "current_coefficients = logistic_model.coef_",
            "new_coefficients = np.full_like(current_coefficients, fill_value=0.5)",
            "logistic_model.coef_ = new_coefficients"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.manifold",
        var_name="embedding",
        import_statements=[
            "from sklearn.datasets import load_digits",
            "from sklearn.manifold import LocallyLinearEmbedding"
        ],
        var_declare_statements=[
            "X, _ = load_digits(return_X_y=True)",
            "embedding = LocallyLinearEmbedding(n_components=2)"
        ],
        var_modify_statements=[
            "X_transformed = embedding.fit_transform(X[:100])"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.metrics",
        var_name="mse",
        import_statements=[
            "from sklearn.metrics import mean_squared_error",
        ],
        var_declare_statements=[
            "y_true = [3, -0.4, 2, 7]",
            "y_pred = [2.5, 0.0, 2, 8]",
            "mse = mean_squared_error(y_true, y_pred)"
        ],
        var_modify_statements=[
            "y_pred[0] = 3",
            "mse = mean_squared_error(y_true, y_pred)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.metrics.pairwise",
        var_name="distance",
        import_statements=[
            "from sklearn.metrics.pairwise import euclidean_distances"
        ],
        var_declare_statements=[
            "X = [[0,1],[1,1]]",
            "distance = euclidean_distances(X,X)"
        ],
        var_modify_statements=[
            "distance = euclidean_distances(X, [[0,0]])"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.mixture",
        var_name="gm",
        import_statements=[
            "import numpy as np",
            "from sklearn.mixture import GaussianMixture"
        ],
        var_declare_statements=[
            "X = np.array([[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]])",
            "gm = GaussianMixture(n_components=2, random_state=0).fit(X)"
        ],
        var_modify_statements=[
            "gm.weights_ = np.array([0.6, 0.4])"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.model_selection",
        var_name="group_kfold",
        import_statements=[
            "import numpy as np",
            "from sklearn.model_selection import GroupKFold"
        ],
        var_declare_statements=[
            "X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]])",
            "y = np.array([1, 2, 3, 4, 5, 6])",
            "groups = np.array([0, 0, 2, 2, 3, 3])",
            "group_kfold = GroupKFold(n_splits=2)",
            "value = group_kfold.split(X, y, groups)"
        ],
        var_modify_statements=[
            "group_kfold.n_splits = 3",
            "value = group_kfold.split(X, y, groups)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.multiclass",
        var_name="clf",
        import_statements=[
            "from sklearn.datasets import load_iris",
            "from sklearn.model_selection import train_test_split",
            "from sklearn.multiclass import OneVsOneClassifier",
            "from sklearn.svm import LinearSVC"
        ],
        var_declare_statements=[
            "X, y = load_iris(return_X_y=True)",
            "X_train, X_test, y_train, y_test = train_test_split( X, y, test_size=0.33, shuffle=True, random_state=0)",
            "clf = OneVsOneClassifier(LinearSVC(dual='auto', random_state=0)).fit(X_train, y_train)"
        ],
        var_modify_statements=[
            "clf.feature_names_in_ = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.naive_bayes",
        var_name="clf",
        import_statements=[
            "import numpy as np",
            "from sklearn.naive_bayes import GaussianNB"
        ],
        var_declare_statements=[
            "X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])",
            "Y = np.array([1, 1, 1, 2, 2, 2])",
            "clf = GaussianNB()",
            "clf.fit(X, Y)"
        ],
        var_modify_statements=[
            "clf.class_prior_ = [0.3, 0.7]"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.neighbors",
        var_name="neigh",
        import_statements=[
            "from sklearn.neighbors import KNeighborsClassifier"
        ],
        var_declare_statements=[
            "X = [[0], [1], [2], [3]]",
            "y = [0, 0, 1, 1]",
            "neigh = KNeighborsClassifier(n_neighbors=3)",
            "neigh.fit(X, y)"
        ],
        var_modify_statements=[
            "neigh.effective_metric_ = 'manhattan'"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.neural_network",
        var_name="clf",
        import_statements=[
            "from sklearn.neural_network import MLPClassifier",
            "from sklearn.datasets import make_classification",
            "from sklearn.model_selection import train_test_split"
        ],
        var_declare_statements=[
            "X, y = make_classification(n_samples=100, random_state=1)",
            "X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=1)",
            "clf = MLPClassifier(random_state=1, max_iter=300).fit(X_train, y_train)"
        ],
        var_modify_statements=[
            "clf.n_iter_ = 200",
            "clf.hidden_layer_sizes = (100,)",
            "clf.learning_rate_init = 0.01"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.pipeline",
        var_name="pipeline",
        import_statements=[
            "from sklearn.naive_bayes import GaussianNB",
            "from sklearn.preprocessing import StandardScaler",
            "from sklearn.pipeline import make_pipeline"
        ],
        var_declare_statements=[
            "pipeline = make_pipeline(StandardScaler(), GaussianNB(priors=None))"
        ],
        var_modify_statements=[
            "pipeline.steps[1] = ('gaussian_nb', GaussianNB(priors=[0.3, 0.7]))"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.preprocessing",
        var_name="drop_enc",
        import_statements=[
            "from sklearn.preprocessing import OneHotEncoder"
        ],
        var_declare_statements=[
            "X = [['Female', 1], ['Male', 2]]",
            "drop_enc = OneHotEncoder(drop='first').fit(X)"
        ],
        var_modify_statements=[
            "drop_enc.drop = 'if_binary'"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.random_projection",
        var_name="transformer",
        import_statements=[
            "import numpy as np",
            "from sklearn.random_projection import GaussianRandomProjection"
        ],
        var_declare_statements=[
            "rng = np.random.RandomState(42)",
            "X = rng.rand(25, 3000)",
            "transformer = GaussianRandomProjection(random_state=rng)",
            "X_new = transformer.fit_transform(X)"
        ],
        var_modify_statements=[
            "transformer.n_components = 1000",
            "transformer.eps = 0.1"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.svm",
        var_name="clf",
        import_statements=[
            "from sklearn.svm import LinearSVC",
            "from sklearn.pipeline import make_pipeline",
            "from sklearn.preprocessing import StandardScaler",
            "from sklearn.datasets import make_classification"
        ],
        var_declare_statements=[
            "X, y = make_classification(n_features=4, random_state=0)",
            "clf = make_pipeline(StandardScaler(),LinearSVC(dual='auto', random_state=0, tol=1e-5))",
            "clf.fit(X, y)"
        ],
        var_modify_statements=[
            "clf.named_steps['linearsvc'].C = 0.1",
            "clf.named_steps['standardscaler'].with_mean = False"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.tree",
        var_name="clf",
        import_statements=[
            "from sklearn.datasets import load_iris",
            "from sklearn.model_selection import cross_val_score",
            "from sklearn.tree import DecisionTreeClassifier"
        ],
        var_declare_statements=[
            "clf = DecisionTreeClassifier(random_state=0)",
            "iris = load_iris()",
            "scores = cross_val_score(clf, iris.data, iris.target, cv=10)"
        ],
        var_modify_statements=[
            "clf.max_depth = 5",
            "clf.min_samples_split = 2"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-learn",
        class_name="sklearn.utils",
        var_name="y",
        import_statements=[
            "import numpy as np",
            "from scipy.sparse import coo_matrix",
            "from sklearn.utils import shuffle"
        ],
        var_declare_statements=[
            "X = np.array([[1., 0.], [2., 1.], [0., 0.]])",
            "y = np.array([0, 1, 2])",
            "X_sparse = coo_matrix(X)"
        ],
        var_modify_statements=[
            "X, X_sparse, y = shuffle(X, X_sparse, y, random_state=0)",
            "shuffle(y, n_samples=2, random_state=0)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.sparse",
        var_name="sparse",
        import_statements=[
            "import numpy as np",
            "from scipy import sparse"
        ],
        var_declare_statements=[
            "dense = np.array([[1, 0, 0, 2], [0, 4, 1, 0], [0, 0, 5, 0]])",
            "sparse = sparse.coo_array(dense)",
        ],
        var_modify_statements=["sparse.data[2] = 100"]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.spatial",
        var_name="tri",
        import_statements=[
            "import numpy as np",
            "from scipy.spatial import Delaunay"
        ],
        var_declare_statements=[
            "points = np.array([[0, 0], [0, 1.1], [1, 0], [1, 1]])",
            "tri = Delaunay(points)"
        ],
        var_modify_statements=[
            "new_points = np.array([[0.5, 0.5], [0.2, 0.8], [0.8, 0.2]])",
            "tri = Delaunay(np.concatenate((points, new_points)))"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.spatial",
        var_name="hull",
        import_statements=[
            "import numpy as np",
            "from scipy.spatial import ConvexHull",
            "rng = np.random.default_rng()"
        ],
        var_declare_statements=[
            "points = rng.random((30, 2))",
            "hull = ConvexHull(points)"
        ],
        var_modify_statements=[
            "new_points = rng.random((10, 2))", 
            "hull = ConvexHull(np.concatenate((points, new_points)))"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.interpolate",
        var_name="y",
        import_statements=[
            "import numpy as np",
            "from scipy.interpolate import CubicSpline"
        ],
        var_declare_statements=[
            "x = np.linspace(0, 10, 10)",
            "y = np.sin(x)",
            "cs = CubicSpline(x, y)"
        ],
        var_modify_statements=[
            "x_new = np.linspace(0, 10, 100)",
            "y = cs(x_new)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.ndimage",
        var_name="a",
        import_statements=[
            "import numpy as np",
            "from scipy import ndimage"
        ],
        var_declare_statements=[
            "a = np.array([[1, 2, 0, 0], [5, 3, 0, 4], [0, 0, 0, 7], [9, 3, 0, 0]])",
            "k = np.array([[1, 1, 1], [1, 1, 0], [1, 0, 0]])"
        ],
        var_modify_statements=[
            "a = ndimage.convolve(a, k, mode='constant', cval=0.0)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.ndimage.interpolate",
        var_name="img",
        import_statements=[
            "import numpy as np",
            "from scipy import ndimage, datasets"
        ],
        var_declare_statements=[
            "img = datasets.ascent()"
        ],
        var_modify_statements=[
            "img = ndimage.rotate(img, 45, reshape=False)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.optimize",
        var_name="x",
        import_statements=[
            "from scipy.optimize import minimize, rosen"
        ],
        var_declare_statements=[
            "x= [1.3, 0.7, 0.8, 1.9, 1.2]",
            "res = minimize(rosen, x, method='Nelder-Mead', tol=1e-6)"
        ],
        var_modify_statements=[
            "x = res.x"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.signal",
        var_name="filt",
        import_statements=[
            "from scipy import signal",
            "import numpy as np"
        ],
        var_declare_statements=[
            "fs = 100",
            "bf = 2 * np.pi * np.array([7, 13])",
            "filt = signal.lti(*signal.butter(4, bf, btype='bandpass',analog=True))",
        ],
        var_modify_statements=[
            "filt = signal.lti(*signal.bilinear(filt.num, filt.den, fs))"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.signal.windows",
        var_name="window",
        import_statements=[
            "import numpy as np",
            "from scipy.signal.windows import general_cosine, gaussian"
        ],
        var_declare_statements=[
            "HFT90D = [1, 1.942604, 1.340318, 0.440811, 0.043097]",
            "window = general_cosine(1000, HFT90D, sym=False)"
        ],
        var_modify_statements=[
            "window = gaussian(51, std=7)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.spatial.distance._hausdorff",
        var_name="dh",
        import_statements=[
            "import numpy as np",
            "from scipy.spatial.distance import directed_hausdorff",
        ],
        var_declare_statements=[
            "u = np.array([(1.0, 0.0),(0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)])",
            "v = np.array([(2.0, 0.0),(0.0, 2.0), (-2.0, 0.0), (0.0, -4.0)])",
            "dh = directed_hausdorff(u, v)[0]"
        ],
        var_modify_statements=[
            "dh = directed_hausdorff(v, u)[0]"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.spatial.distance",
        var_name="eu",
        import_statements=[
            "from scipy.spatial import distance",
        ],
        var_declare_statements=[
            "eu = distance.euclidean([1,0,0], [0,1,0])"
        ],
        var_modify_statements=[
            "eu = distance.euclidean([1,1,0], [0,1,0])"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.special",
        var_name="result",
        import_statements=[
            "import numpy as np",
            "from scipy.special import rel_entr, kl_div"
        ],
        var_declare_statements=[
            "p = np.array([0.1, 0.2, 0.3, 0.4])",
            "q = np.array([0.15, 0.25, 0.3, 0.3])",
            "result = rel_entr(p, q)"
        ],
        var_modify_statements=[
            "result = kl_div(p, q)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scipy",
        class_name="scipy.stats",
        var_name="result",
        import_statements=[
            "import numpy as np",
            "from scipy import stats"
        ],
        var_declare_statements=[
            "rng = np.random.default_rng()",
            "x = rng.random(10)",
            "y = 1.6*x + rng.random(10)",
            "result = stats.linregress(x, y)"
        ],
        var_modify_statements=[
            "y[0] += 1",
            "result = stats.linregress(x, y)"
        ]
    ),
    LibCoverageTestCase(
        module_name="seaborn",
        class_name="seaborn",
        var_name="ax",
        import_statements=[
            "import seaborn as sns"
        ],
        var_declare_statements=[
            "tips = sns.load_dataset('tips')",
            "ax = sns.histplot(data=tips, x='total_bill', bins=10)"
        ],
        var_modify_statements=[
            "ax = sns.histplot(data=tips, x='total_bill', bins=11)"
        ]
    ),
    #LibCoverageTestCase(
    #    module_name="shap",
    #    class_name="shap",
    #    var_name="explainer",
    #    import_statements=[
    #        "import xgboost",
    #        "import shap",
    #    ],
    #    var_declare_statements=[
    #        "X, y = shap.datasets.adult()",
    #        "model = xgboost.XGBClassifier()",
    #        "model.fit(X, y)",
    #        "explainer = shap.explainers.Exact(model.predict_proba, X)",
    #        "new_model = xgboost.XGBRegressor()",
    #        "new_model.fit(X, y)",
    #    ],
    #    var_modify_statements=[
    #        "explainer.model = new_model"
    #    ]
    #),
    LibCoverageTestCase(
        module_name="scikit-image",
        class_name="skimage",
        var_name="image",
        import_statements=[
            "from skimage.data import astronaut",
            "from skimage.filters import gaussian"
        ],
        var_declare_statements=[
            "image = astronaut()"
        ],
        var_modify_statements=[
            "image = gaussian(image, sigma=1, channel_axis=-1)"
        ]
    ),
    LibCoverageTestCase(
        module_name="scikit-image",
        class_name="skimage.morphology",
        var_name="f",
        import_statements=[
            "import numpy as np",
            "from skimage.morphology import area_opening"
        ],
        var_declare_statements=[
            "w = 12",
            "x, y = np.mgrid[0:w,0:w]",
            "f = 20 - 0.2*((x - w/2)**2 + (y-w/2)**2)",
            "f[2:3,1:5] = 40",
            "f[2:4,9:11] = 60",
            "f[9:11,2:4] = 80",
            "f[9:10,9:11] = 100",
            "f[10,10] = 100",
            "f = f.astype(int)"
        ],
        var_modify_statements=[
            "f = area_opening(f, 8, connectivity=1)"
        ]
    ),
    LibCoverageTestCase(
        module_name="statsmodels",
        class_name="statsmodels.api",
        var_name="gamma_model",
        import_statements=[
            "import statsmodels.api as sm"
        ],
        var_declare_statements=[
            "data = sm.datasets.scotland.load()",
            "data.exog = sm.add_constant(data.exog)",
            "gamma_model = sm.GLM(data.endog, data.exog, family=sm.families.Gamma())"
        ],
        var_modify_statements=[
            "gamma_model.family = sm.families.InverseGaussian()"
        ]
    ),
    LibCoverageTestCase(
        module_name="tensorflow",
        class_name="tensorflow",
        var_name="tensor",
        import_statements=[
            "import tensorflow as tf"
        ],
        var_declare_statements=[
            "tensor = tf.constant([[1, 2], [3, 4]])"
        ],
        var_modify_statements=[
            "tensor = tf.tensor_scatter_nd_update(tensor, indices=[[0, 0]], updates=[5])"
        ]
    ),
    LibCoverageTestCase(
        module_name="tensorflow",
        class_name="tensorflow.keras.models",
        var_name="model",
        import_statements=[
            "import tensorflow as tf",
            "from tensorflow.keras.models import Sequential",
            "from tensorflow.keras.layers import Dense"
        ],
        var_declare_statements=[
            "model = Sequential([Dense(10, input_shape=(784,), activation='relu'), Dense(10, activation='softmax')])"
        ],
        var_modify_statements=[
            "model.add(Dense(5, activation='sigmoid'))"
        ]
    ),
    LibCoverageTestCase(
        module_name="tensorflow",
        class_name="tensorflow.keras.optimizers",
        var_name="model",
        import_statements=[
            "import tensorflow as tf",
            "from tensorflow.keras.models import Sequential",
            "from tensorflow.keras.layers import Dense"
        ],
        var_declare_statements=[
            "model = Sequential([Dense(10, input_shape=(784,), activation='relu'), Dense(10, activation='softmax')])",
            "optimizer = tf.keras.optimizers.SGD(learning_rate=0.01)",
            "model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])"
        ],
        var_modify_statements=[
            "optimizer.learning_rate = 0.001",
            "model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])"
        ]
    ),
    LibCoverageTestCase(
        module_name="transformers",
        class_name="transformers",
        var_name="tokenizer",
        import_statements=[
            "from transformers import BertTokenizer"
        ],
        var_declare_statements=[
            "tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')"
        ],
        var_modify_statements=[
            "tokenizer.do_basic_tokenize = False", 
            "tokenizer = BertTokenizer.from_pretrained('bert-base-cased')"
        ]
    ),
    LibCoverageTestCase(
        module_name="tokenizers",
        class_name="tokenizers",
        var_name="tokenizer",
        import_statements=[
            "from tokenizers import Tokenizer",
            "from tokenizers.models import BPE"
        ],
        var_declare_statements=[
            "tokenizer = Tokenizer(BPE())"
        ],
        var_modify_statements=[
            "tokenizer.enable_truncation(max_length=128)",
            "tokenizer = Tokenizer(BPE())"
        ]
    ),
    LibCoverageTestCase(
        module_name="torch",
        class_name="torch",
        var_name="tensor",
        import_statements=[
            "import torch"
        ],
        var_declare_statements=[
            "tensor = torch.tensor([[1, 2], [3, 4]])"
        ],
        var_modify_statements=[
            "tensor[0, 0] = 5"
        ]
    ),
    LibCoverageTestCase(
        module_name="torch",
        class_name="torch.nn",
        var_name="model",
        import_statements=[
            "import torch",
            "import torch.nn as nn"
        ],
        var_declare_statements=[
            "model = nn.Sequential(nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),nn.ReLU(),nn.MaxPool2d(kernel_size=2, stride=2),nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),nn.ReLU(),nn.MaxPool2d(kernel_size=2, stride=2),nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),nn.ReLU(),nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),nn.ReLU(), nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1), nn.ReLU())"
        ],
        var_modify_statements=[
            "model[0] = nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1)",
            "model[-1] = nn.Conv2d(512, 1024, kernel_size=3, stride=1, padding=1)",
            "model.add_module('dropout', nn.Dropout(0.5))"
        ]
    ),
    LibCoverageTestCase(
        module_name="torch",
        class_name="torch.nn.functional",
        var_name="output",
        import_statements=[
            "import torch",
            "import torch.nn.functional as F"
        ],
        var_declare_statements=[
            "output = torch.randn(1, 1, 28, 28)"
        ],
        var_modify_statements=[
            "output = F.conv2d(output, torch.randn(16, 1, 3, 3), stride=1, padding=1)",
            "output = F.max_pool2d(output, kernel_size=2, stride=2)" 
        ]
    ),
    LibCoverageTestCase(
        module_name="torch",
        class_name="torch.optim",
        var_name="optimizer",
        import_statements=[
            "import torch",
            "import torch.nn as nn",
            "import torch.optim as optim"
        ],
        var_declare_statements=[
            "model = nn.Linear(10, 1)",
            "optimizer = optim.SGD(model.parameters(), lr=0.01)",
            "input = torch.randn(1, 10)",
            "target = torch.randn(1)"
        ],
        var_modify_statements=[
            "optimizer.zero_grad()",
            "output = model(input)",
            "loss = nn.MSELoss()(output, target)",
            "loss.backward()",
            "optimizer.step()",
            "optimizer.param_groups[0]['lr'] = 0.001"
        ]
    ),
    LibCoverageTestCase(
        module_name="torch",
        class_name="torch.utils.data",
        var_name="subset",
        import_statements=[
            "import torch",
            "from torch.utils.data import TensorDataset, Subset"
        ],
        var_declare_statements=[
            "data = torch.randn(100, 3, 32, 32)",
            "targets = torch.randint(0, 10, (100,))",
            "dataset = TensorDataset(data, targets)",
            "indices = torch.arange(50)",
            "subset = Subset(dataset, indices)"
        ],
        var_modify_statements=[
            "indices = torch.arange(25)",
            "subset.indices = indices"
        ]
    ),
    LibCoverageTestCase(
        module_name="torchvision",
        class_name="torchvision.datasets",
        var_name="cifar_dataset",
        import_statements=[
            "import torch",
            "from torchvision.datasets import CIFAR10",
            "import torchvision.transforms as tvtf"
        ],
        var_declare_statements=[
            "cifar_dataset = CIFAR10(root='./data', train=True, download=True)"
        ],
        var_modify_statements=[
            "cifar_dataset.transform = tvtf.Compose([tvtf.ToTensor(), tvtf.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])"
        ]
    ),
    LibCoverageTestCase(
        module_name="torchvision",
        class_name="torchvision.transforms",
        var_name="cifar_dataset",
        import_statements=[
            "import torch",
            "from torchvision.datasets import CIFAR10",
            "import torchvision.transforms as tvtf"
        ],
        var_declare_statements=[
            "cifar_dataset = CIFAR10(root='./data', train=True, download=True)"
        ],
        var_modify_statements=[
            "cifar_dataset.transform = tvtf.Compose([tvtf.ToTensor(), tvtf.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])"
        ]
    ),
    LibCoverageTestCase(
        module_name="torchvision",
        class_name="torchvision.utils",
        var_name="image",
        import_statements=[
            "import torchvision.utils as utils",
            "import torch",
        ],
        var_declare_statements=[
            "image = torch.zeros((3, 100, 100), dtype=torch.uint8)"
        ],
        var_modify_statements=[
            "keypoints = [(20, 30), (50, 70), (80, 10)]",
            "image = utils.draw_keypoints(image, keypoints)"
        ]
    ),
    LibCoverageTestCase(
        module_name="plotly",
        class_name="plotly.express",
        var_name="fig",
        import_statements=[
            "import plotly.express as px"
        ],
        var_declare_statements=[
            "data = px.data.iris()",
            "fig = px.scatter(data, x='sepal_width', y='sepal_length', color='species')"
        ],
        var_modify_statements=[
            "fig.update_traces(marker=dict(size=10))"
        ]
    ),
    LibCoverageTestCase(
        module_name="plotly",
        class_name="plotly.graph_objects",
        var_name="bar_chart",
        import_statements=[
            "import plotly.graph_objects as go"
        ],
        var_declare_statements=[
            "bar_chart = go.Figure(data=[go.Bar(x=['A', 'B', 'C'], y=[1, 2, 3])])"
        ],
        var_modify_statements=[
            "bar_chart.update_layout(title='My Bar Chart', xaxis_title='Categories', yaxis_title='Values')"
        ]
    ),
    LibCoverageTestCase(
        module_name="plotly",
        class_name="plotly.figure_factory",
        var_name="table_fig",
        import_statements=[
            "import plotly.figure_factory as ff"
        ],
        var_declare_statements=[
            "data_matrix = [['Country', 'Year', 'Population'], ['US', 2020, 331002651], ['India', 2020, 1380004385], ['China', 2020, 1444216107]]",
            "table_fig = ff.create_table(data_matrix)"
        ],
        var_modify_statements=[
            "table_fig.update_layout(title='Population Data')"
        ]
    ),
    LibCoverageTestCase(
        module_name="plotly",
        class_name="plotly.graph_objs",
        var_name="line_chart",
        import_statements=[
            "import plotly.graph_objs as go"
        ],
        var_declare_statements=[
            "line_chart = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))"
        ],
        var_modify_statements=[
            "line_chart.update_layout(title='Line Chart', xaxis_title='X-axis', yaxis_title='Y-axis')"
        ]
    ),
    LibCoverageTestCase(
        module_name="plotly",
        class_name="plotly.io",
        var_name="html_fig",
        import_statements=[
            "import plotly.io as pio",
            "import plotly.graph_objects as go"
        ],
        var_declare_statements=[
            "fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))",
            "html_fig = pio.to_html(fig)"
        ],
        var_modify_statements=[
            "html_fig += '<p>This is an HTML plot.</p>'"
        ]
    ),
    LibCoverageTestCase(
        module_name="plotly",
        class_name="plotly.offline",
        var_name="offline_fig",
        import_statements=[
            "import plotly.offline as pyo",
            "import plotly.graph_objects as go"
        ],
        var_declare_statements=[
            "fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))",
            "offline_fig = pyo.plot(fig, output_type='div')"
        ],
        var_modify_statements=[
            "offline_fig += '<p>This is an offline plot.</p>'"
        ]
    ),
    LibCoverageTestCase(
        module_name="plotly",
        class_name="plotly.subplots",
        var_name="subplot_fig",
        import_statements=[
            "from plotly.subplots import make_subplots",
            "import plotly.graph_objects as go"
        ],
        var_declare_statements=[
            "subplot_fig = make_subplots(rows=2, cols=2, subplot_titles=('Plot 1', 'Plot 2', 'Plot 3', 'Plot 4'))",
            "subplot_fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]), row=1, col=1)",
            "subplot_fig.add_trace(go.Scatter(x=[1, 2, 3], y=[6, 5, 4]), row=1, col=2)",
            "subplot_fig.add_trace(go.Scatter(x=[1, 2, 3], y=[2, 4, 6]), row=2, col=1)",
            "subplot_fig.add_trace(go.Scatter(x=[1, 2, 3], y=[8, 6, 4]), row=2, col=2)"
        ],
        var_modify_statements=[
            "subplot_fig.update_layout(title='Subplot Title')"
        ]
    ),
    LibCoverageTestCase(
        module_name="polars",
        class_name="polars.DataFrame",
        var_name="df",
        import_statements=[
            "import polars as pl"
        ],
        var_declare_statements=[
            "df = pl.DataFrame({'A': [1, 2, 3, 4], 'B': [5, 6, 7, 8]})"
        ],
        var_modify_statements=[
            "df = df.select(['B', 'A'])" 
        ]
    ),
    LibCoverageTestCase(
        module_name="polars",
        class_name="polars.LazyFrame",
        var_name="lf",
        import_statements=[
            "import polars as pl"
        ],
        var_declare_statements=[
            "lf = pl.DataFrame({'A': [1, 2, 3, 4], 'B': [5, 6, 7, 8]}).lazy()"
        ],
        var_modify_statements=[
            "lf = lf.filter(pl.col('A') > 2)"
        ]
    ),
    LibCoverageTestCase(
        module_name="prophet",
        class_name="prophet.Prophet",
        var_name="m",
        import_statements=[
            "from prophet import Prophet",
            "import pandas as pd",
            "import numpy as np"
        ],
        var_declare_statements=[
            "np.random.seed(42)",
            "dates = pd.date_range(start='2022-01-01', end='2022-12-31', freq='D')",
            "df = pd.DataFrame({'ds': dates, 'y': np.random.randn(len(dates))})",
            "m = Prophet()"
        ],
        var_modify_statements=[
            "m.add_seasonality(name='monthly', period=30.5, fourier_order=5)",
            "m.fit(df)"
        ]
    ),
    LibCoverageTestCase(
        module_name="pyspark",
        class_name="pyspark.sql",
        var_name="result",
        import_statements=[
            "import pandas as pd",
            "from pyspark.sql import SparkSession"
        ],
        var_declare_statements=[
            "spark = SparkSession.builder.master('local[2]').appName('test').getOrCreate()",
            "df = spark.createDataFrame([(1, 'Alice'), (2, 'Bob'), (3, 'Charlie')], ['id', 'name'])",
            "df.createOrReplaceTempView('people')",
            "result = spark.sql('SELECT * FROM people').toPandas()"
        ],
        var_modify_statements=[
            "result = spark.sql('SELECT * FROM people WHERE id > 1').toPandas()",
        ]
    ),
    #LibCoverageTestCase(
    #    module_name="xgboost",
    #    class_name="xgboost.XGBRegressor",
    #    var_name="model",
    #    import_statements=[
    #        "import numpy as np",
    #        "import xgboost"
    #    ],
    #    var_declare_statements=[
    #        "X_train = np.random.rand(100, 10)",
    #        "y_train = np.random.rand(100)",
    #        "model = xgboost.XGBRegressor()",
    #        "model.fit(X_train, y_train)"
    #    ],
    #    var_modify_statements=[
    #        "model.learning_rate = 0.1",
    #    ]
    #),
    LibCoverageTestCase(
        module_name="catboost",
        class_name="catboost",
        var_name="clf",
        import_statements=[
            "from catboost import CatBoostClassifier",
            "from sklearn.datasets import make_classification",
            "from sklearn.model_selection import train_test_split"
        ],
        var_declare_statements=[
            "X, y = make_classification(n_samples=1000, n_features=20, random_state=42)",
            "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)",
            "clf = CatBoostClassifier(iterations=50, depth=3, learning_rate=0.1, random_seed=42)"
        ],
        var_modify_statements=[
            "clf.learning_rate = 0.05", 
            "clf.fit(X_train, y_train)"
        ]
    ),
    LibCoverageTestCase(
        module_name="opencv-python",
        class_name="cv2",
        var_name="image",
        import_statements=[
            "import cv2"
        ],
        var_declare_statements=[
            "image = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'",
        ],
        var_modify_statements=[
            "image = cv2.CascadeClassifier(image)"
        ]
    ),
    LibCoverageTestCase(
        module_name="gensim",
        class_name="gensim",
        var_name="model",
        import_statements=[
            "import gensim"
        ],
        var_declare_statements=[
            "data = [['this', 'is', 'the', 'first', 'sentence', 'for', 'word2vec'],['this', 'is', 'the', 'second', 'sentence'],['yet', 'another', 'sentence'],['one', 'more', 'sentence'],['and', 'the', 'final', 'sentence']]",
            "model = gensim.models.Word2Vec(data, min_count=1)"
        ],
        var_modify_statements=[
            "model.min_count = 2"
        ]
    ),
    LibCoverageTestCase(
        module_name="gym",
        class_name="gym",
        var_name="env",
        import_statements=[
            "import gym"
        ],
        var_declare_statements=[
            "env = gym.make('CartPole-v1')"
        ],
        var_modify_statements=[
            "env.max_episode_steps = 500"
        ]
    ),
    LibCoverageTestCase(
        module_name="transformers",
        class_name="huggingface",
        var_name="model",
        import_statements=[
            "from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer"
        ],
        var_declare_statements=[
            "classifier = pipeline('sentiment-analysis')",
            "text = 'I love using Hugging Face Transformers!'",
            "model_name = 'distilbert-base-uncased'",
            "model = AutoModelForSequenceClassification.from_pretrained(model_name)"
        ],
        var_modify_statements=[
            "model.config.num_labels = 3"
        ]
    ),

    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.colors.ListedColormap",
        var_name="cmap",
        import_statements=["from matplotlib.colors import ListedColormap"],
        var_declare_statements=["cmap = ListedColormap(['r', 'g', 'b'])"],
        var_modify_statements=["cmap.N = 10"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.colors.BoundaryNorm",
        var_name="norm",
        import_statements=["from matplotlib.colors import BoundaryNorm, ListedColormap"],
        var_declare_statements=["cmap = ListedColormap(['r', 'g', 'b'])",
                                "norm = BoundaryNorm([-1, -0.5, 0.5, 1], cmap.N)"],
        var_modify_statements=["norm.N = 10"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.dates.WeekdayLocator",
        var_name="loc",
        import_statements=["from matplotlib.dates import MO, TU, WE, TH, FR, SA, SU, WeekdayLocator"],
        var_declare_statements=["loc = WeekdayLocator(byweekday=MO)"],
        var_modify_statements=["loc.tz = 'Africa/Abidjan'"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.dates.AutoDateFormatter",
        var_name="formatter",
        import_statements=["from matplotlib.dates import WeekdayLocator, AutoDateLocator, AutoDateFormatter"],
        var_declare_statements=["locator = AutoDateLocator()",
                                "formatter = AutoDateFormatter(locator)"],
        var_modify_statements=["formatter.scaled[1/(24*60)] = '%M:%S'"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.lines.Line2D",
        var_name="markerline",
        import_statements=["import matplotlib.pyplot as plt", "import numpy as np"],
        var_declare_statements=["plt.close('all')",
                                "x = np.linspace(0.1, 2 * np.pi, 41)",
                                "y = np.exp(np.sin(x))",
                                "markerline, stemlines, baseline = plt.stem(x, y, linefmt='grey', markerfmt='D', bottom=1.1)"],
        var_modify_statements=["markerline.set_markerfacecolor('none')"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.patches.Ellipse",
        var_name="e1",
        import_statements=["import matplotlib.pyplot as plt",
                           "from matplotlib import patches"],
        var_declare_statements=["plt.close('all')",
                                "xcenter, ycenter = 0.38, 0.52",
                                "width, height = 1e-1, 3e-1",
                                "angle = -30",
                                "e1 = patches.Ellipse((xcenter, ycenter), width, height,angle=angle, linewidth=2, fill=False, zorder=2)"],
        var_modify_statements=["e1.set_center((2.0,3.0))"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.patches.Arrow",
        var_name="arrow",
        import_statements=["import matplotlib.pyplot as plt", "import matplotlib.patches as mpatches"],
        var_declare_statements=["plt.close('all')",
                                "x_tail, y_tail = 0.1, 0.5",
                                "x_head, y_head = 0.9, 0.8",
                                "arrow = mpatches.FancyArrowPatch((x_tail, y_tail), (x_head, y_head),mutation_scale=100)"],
        var_modify_statements=["arrow.set_linewidth(2.0)"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.image.AxesImage",
        var_name="image",
        import_statements=["import matplotlib.pyplot as plt", "import numpy as np"],
        var_declare_statements=["plt.close('all')",
                                "data = np.random.rand(10,10)",
                                "fig, ax = plt.subplots()",
                                "image = ax.imshow(data, cmap='viridis')"],
        var_modify_statements=["image.set_cmap('plasma')"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.image.FigureImage",
        var_name="fig_image",
        import_statements=["import matplotlib.pyplot as plt", "import numpy as np"],
        var_declare_statements=["plt.close('all')",
                                "data = np.random.rand(10,10)",
                                "fig = plt.figure()",
                                "fig_image = fig.figimage(data)"],
        var_modify_statements=["fig_image.set_x(100)"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.offsetbox.AnchoredOffsetbox",
        var_name="anchored_box",
        import_statements=["import matplotlib.pyplot as plt", "from matplotlib.offsetbox import AnchoredOffsetbox, TextArea"],
        var_declare_statements=["plt.close('all')",
                                "fig, ax = plt.subplots()",
                                "text_area = TextArea('Hello, World!', textprops=dict(color='r', size=12, ha='left'))",
                                "anchored_box = AnchoredOffsetbox(loc='upper left', child=text_area, pad=0.5, borderpad=0.5, frameon=True)"],
        var_modify_statements=["anchored_box.patch.set_facecolor('lightblue')"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="matplotlib.ticker.AutoLocator",
        var_name="aut",
        import_statements=["import matplotlib.pyplot as plt", "from matplotlib.ticker import AutoLocator"],
        var_declare_statements=["plt.close('all')",
                                "fig, ax = plt.subplots()",
                                "ax.plot([0, 5], [0, 200])",
                                "aut=AutoLocator()"],
        var_modify_statements=["aut.MAXTICKS=2000"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.coordinates.SkyCoord",
        var_name="icrs",
        import_statements=["import astropy.coordinates as coord", "import astropy.units as u"],
        var_declare_statements=["icrs = coord.SkyCoord(ra=258.58356362 * u.deg, dec=14.55255619 * u.deg, radial_velocity=-16.1 * u.km / u.s, frame='icrs',)"],
        var_modify_statements=["icrs = SkyCoord(ra=260.0 * u.deg, dec=icrs.dec, radial_velocity=icrs.radial_velocity, frame='icrs',)"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.io.fits.HDUList",
        var_name="new_hdul",
        import_statements=["from astropy.io import fits"],
        var_declare_statements=["new_hdul = fits.HDUList()"],
        var_modify_statements=["new_hdul.append(fits.ImageHDU())"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.io.fits.PrimaryHDU",
        var_name="hdu1",
        import_statements=["from astropy.io import fits"],
        var_declare_statements=["hdu1 = fits.PrimaryHDU()"],
        var_modify_statements=["hdu1.add_checksum()"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.modeling.functional_models.Linear1D",
        var_name="line_orig",
        import_statements=["from astropy.modeling.models import Linear1D"],
        var_declare_statements=["line_orig = Linear1D(slope=1.0, intercept=0.5)"],
        var_modify_statements=["line_orig.slope=3"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.modeling.functional_models.Ellipse2D",
        var_name="e",
        import_statements=["from astropy.modeling.models import Ellipse2D",
                           "from astropy.coordinates import Angle"],
        var_declare_statements=["e = Ellipse2D(amplitude=100., x_0=25, y_0=25, a=20, b=10, theta=Angle(30, 'deg').radian)"],
        var_modify_statements=["e.x_0=50"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.modeling.fitting.LinearLSQFitter",
        var_name="fit",
        import_statements=["from astropy.modeling import models, fitting"],
        var_declare_statements=["fit = fitting.LinearLSQFitter()"],
        var_modify_statements=["fit.calc_uncertainties=True"]
    ), 
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.modeling.polynomial.Polynomial1D",
        var_name="poly",
        import_statements=["from astropy.modeling.polynomial import Polynomial1D"],
    var_declare_statements=["poly = Polynomial1D(3)"],
        var_modify_statements=["poly.n_inputs = 3"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.modeling.polynomial.Polynomial2D",
        var_name="poly2d",
        import_statements=["from astropy.modeling.polynomial import Polynomial2D"],
        var_declare_statements=["poly2d = Polynomial2D(5)"],
        var_modify_statements=["poly2d.x_domain = (-5,5)"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.nddata.NDData",
        var_name="nd",
        import_statements=["from astropy.nddata import NDData",
                           "import numpy as np"],
        var_declare_statements=["array = np.zeros((12, 12, 12))",
                                "nd = NDData(array)"],
        var_modify_statements=["nd.data[0,0,0] = 49"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.nddata.NDDataRef",
        var_name="ndd1",
        import_statements=["from astropy.nddata import NDDataRef, StdDevUncertainty",
                           "import numpy as np"],
        var_declare_statements=["data = np.ones((3,3), dtype=float)", 
                                "ndd1 = NDDataRef(data, uncertainty=StdDevUncertainty(data))"],
        var_modify_statements=["ndd1.data[0,0] = 100"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.stats.SigmaClip",
        var_name="sigclip",
        import_statements=["from astropy.stats import SigmaClip",
                           "from numpy.random import randn"],
        var_declare_statements=["randvar = randn(10000)",
                                "sigclip = SigmaClip(sigma=2, maxiters=5)"],
        var_modify_statements=["sigclip.sigma=3"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.table.QTable",
        var_name="t",
        import_statements=["from astropy.table import QTable",
                           "import numpy as np",
                           "import astropy.units as u"],
        var_declare_statements=["a = np.array([1, 4, 5], dtype=np.int32)",
                                "b = [2.0, 5.0, 8.5]",
                                "c = ['x', 'y', 'z']",
                                "d = [10, 20, 30] * u.m / u.s",
                                "t = QTable([a, b, c, d],names=('a', 'b', 'c', 'd'),meta={'name': 'first table'})"],
        var_modify_statements=["e = [10.0, 115.0, 9.5]",
                               "t.add_column(e)"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.units.Quantity",
        var_name="q",
        import_statements=["from astropy import units as u"],
        var_declare_statements=["q = [1, 2] * u.m"],
        var_modify_statements=["q.value[1]=100"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.visualization.PercentileInterval",
        var_name="interval",
        import_statements=["from astropy.visualization import PercentileInterval"],
        var_declare_statements=["interval = PercentileInterval(50.)"],
        var_modify_statements=["interval.n_samples=10"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.visualization.mpl_normalize.ImageNormalize",
        var_name="norm",
        import_statements=["from astropy.visualization import (MinMaxInterval, SqrtStretch,ImageNormalize)",
                           "import numpy as np"],
        var_declare_statements=["image = np.arange(65536).reshape((256, 256))", 
                                "norm = ImageNormalize(image, interval=MinMaxInterval(),stretch=SqrtStretch())"],
        var_modify_statements=["norm.vmin=10"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.wcs.WCS",
        var_name="w",
        import_statements=["from astropy.io import fits", 
                           "from astropy.wcs import WCS",
                           "from astropy.utils.data import get_pkg_data_filename"],
        var_declare_statements=["fn = get_pkg_data_filename('data/j94f05bgq_flt.fits', package='astropy.wcs.tests')",
                                "f = fits.open(fn)",
                                "w = WCS(f[1].header)"],
        var_modify_statements=["w.wcs.crpix = [100, 100]"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.wcs.Celprm",
        var_name="celprm",
        import_statements=["from astropy.wcs import Celprm"],
        var_declare_statements=["celprm = Celprm()"],
        var_modify_statements=["celprm.ref = [180.0, 90.0]"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.convolution.Box2DKernel",
        var_name="box_2D_kernel",
        import_statements=["from astropy.convolution import Box2DKernel"],
        var_declare_statements=["box_2D_kernel = Box2DKernel(9)"],
        var_modify_statements=["box_2D_kernel.array[0][0] = 0.05"]
    ),
    LibCoverageTestCase(
        module_name="astropy",
        class_name="astropy.convolution.Gaussian2DKernel",
        var_name="gaussian_2D_kernel",
        import_statements=["from astropy.convolution import Gaussian2DKernel"],
        var_declare_statements=["gaussian_2D_kernel = Gaussian2DKernel(10)"],
        var_modify_statements=["gaussian_2D_kernel.array[1][2] = 0.003"]
    ),
    LibCoverageTestCase(
        module_name="numpy",
        class_name="numpy.ndarray",
        var_name="a",
        import_statements=["import numpy as np"],
        var_declare_statements=["a = np.arange(6)"],
        var_modify_statements=["a[1]=20"]
    ),
    LibCoverageTestCase(
        module_name="arrow",
        class_name="arrow.arrow.Arrow",
        var_name="utc",
        import_statements=["import arrow"],
        var_declare_statements=["utc = arrow.utcnow()"],
        var_modify_statements=["utc = utc.shift(hours=-1)"]
    ),
    LibCoverageTestCase(
        module_name="bokeh",
        class_name="bokeh.plotting._figure.figure",
        var_name="p",
        import_statements=["from bokeh.plotting import figure, show"],
        var_declare_statements=["p = figure(width=400, height=400)"],
        var_modify_statements=["p.height=600"]
    ),
    LibCoverageTestCase(
        module_name="bokeh",
        class_name="bokeh.models.renderers.glyph_renderer.GlyphRenderer",
        var_name="r",
        import_statements=["from bokeh.plotting import figure"],
        var_declare_statements=["plot = figure(title='Example Plot', x_axis_label='X-Axis', y_axis_label='Y-Axis')",
                                "r = plot.circle([1,2,3], [4,5,6])"],
        var_modify_statements=["r.tags = ['foo', 10]"]
    ),
    LibCoverageTestCase(
        module_name="photoutils",
        class_name="photutils.utils.CutoutImage",
        var_name="cutout",
        import_statements=["import numpy as np",
                           "from photutils.utils import CutoutImage"],
        var_declare_statements=["data = np.arange(20.0).reshape(5, 4)",
                                "cutout = CutoutImage(data, (2, 2), (3, 3))"],
        var_modify_statements=["cutout.position = (2,3)"]
    ),
    LibCoverageTestCase(
        module_name="photoutils",
        class_name="photutils.utils.ImageDepth",
        var_name="depth",
        import_statements=["from astropy.convolution import convolve",
                           "from astropy.visualization import simple_norm", 
                           "from photutils.datasets import make_100gaussians_image",
                           "from photutils.segmentation import SourceFinder, make_2dgaussian_kernel",
                           "from photutils.utils import ImageDepth"],
        var_declare_statements=["bkg = 5.0", 
                                "data = make_100gaussians_image() - bkg", 
                                "kernel = make_2dgaussian_kernel(3.0, size=5)", 
                                "convolved_data = convolve(data, kernel)",
                                "npixels = 10",
                                "threshold = 3.2", 
                                "finder = SourceFinder(npixels=npixels, progress_bar=False)", 
                                "segment_map = finder(convolved_data, threshold)", 
                                "mask = segment_map.make_source_mask()", 
                                "radius = 4",
                                "depth = ImageDepth(radius, nsigma=5.0, napers=500, niters=2,overlap=False, seed=123, zeropoint=23.9,progress_bar=False)"],
        var_modify_statements=["depth.aper_radius = 10"]
    ),
    LibCoverageTestCase(
        module_name="photoutils",
        class_name="photutils.psf.matching.HanningWindow",
        var_name="taper",
        import_statements=["import matplotlib.pyplot as plt",
                           "from photutils.psf import HanningWindow"],
        var_declare_statements=["taper = HanningWindow()"],
        var_modify_statements=["taper.alpha = 2.0"]
    ),
    LibCoverageTestCase(
        module_name="photoutils",
        class_name="photutils.psf.matching.CosineBellWindow",
        var_name="taper",
        import_statements=["import matplotlib.pyplot as plt",
                           "from photutils.psf import CosineBellWindow"],
        var_declare_statements=["taper = CosineBellWindow(alpha=0.3)"],
        var_modify_statements=["taper.beta = 1.0"]
    ),
    LibCoverageTestCase(
        module_name="optuna",
        class_name="optuna.Study",
        var_name="study",
        import_statements=["import optuna"],
        var_declare_statements=["def objective(trial):\n    x = trial.suggest_float('x', -10, 10)\n    return (x - 2) ** 2",
                                "study = optuna.create_study()"],
        var_modify_statements=["study.optimize(objective, n_trials=100)"]
    ),
    LibCoverageTestCase(
        module_name="keras",
        class_name="keras.src.layers.core.dense.Dense",
        var_name="layer",
        import_statements=["from keras import layers",
                           "import numpy as np"],
        var_declare_statements=["layer = layers.Dense(units=64)",
                                "layer.build((10,))"],
        var_modify_statements=["weights = np.random.rand(10, 64)",
                               "biases = np.random.rand(64)",
                               "layer.set_weights([weights, biases])"]
    ),
    LibCoverageTestCase(
        module_name="keras",
        class_name="keras.src.initializers.initializers.RandomNormal",
        var_name="kernel_initializer",
        import_statements=["from keras import layers",
                           "from keras import initializers"],
        var_declare_statements=["kernel_initializer=initializers.RandomNormal(stddev=0.01)"],
        var_modify_statements=["kernel_initializer.mean = 1.0"]
    ),
    LibCoverageTestCase(
        module_name="keras",
        class_name="keras.src.initializers.initializers.RandomUniform",
        var_name="kernel_initializer",
        import_statements=["from keras import layers",
                           "from keras import initializers"],
        var_declare_statements=["kernel_initializer = initializers.RandomUniform(minval=-0.05, maxval=0.05, seed=None)"],
        var_modify_statements=["kernel_initializer.seed = 1"]
    ),
    LibCoverageTestCase(
        module_name="keras",
        class_name="keras.src.optimizers.adam.Adam",
        var_name="opt",
        import_statements=["import keras"],
        var_declare_statements=["opt = keras.optimizers.Adam(learning_rate=0.01)"],
        var_modify_statements=["opt.ema_momentum = 0.9"]
    ),
    LibCoverageTestCase(
        module_name="keras",
        class_name="keras.src.optimizers.schedules.learning_rate_schedule.ExponentialDecay",
        var_name="lr_schedule",
        import_statements=["import keras"],
        var_declare_statements=["lr_schedule = keras.optimizers.schedules.ExponentialDecay(initial_learning_rate=1e-2,decay_steps=10000,decay_rate=0.9)"],
        var_modify_statements=["lr_schedule.decay_rate = 0.5"]
    ),
    LibCoverageTestCase(
        module_name="llm",
        class_name="llm.default_plugins.openai_models.Chat",
        var_name="model",
        import_statements=["import llm"],
        var_declare_statements=["model = llm.get_model('gpt-3.5-turbo')"],
        var_modify_statements=["model.key = 'ABCD'"]
    ),
    LibCoverageTestCase(
        module_name="lmfit",
        class_name="lmfit.parameter.Parameters",
        var_name="params",
        import_statements=["from lmfit import Parameters"],
        var_declare_statements=["params = Parameters()"],
        var_modify_statements=["params.add('amp', value=10, vary=False)"]
    ),
    LibCoverageTestCase(
        module_name="matplotlib",
        class_name="'mpl_toolkits.mplot3d.art3d.Line3DCollection",
        var_name="pl1",
        import_statements=["import numpy as np",
                           "import matplotlib.pyplot as plt",
                           "from matplotlib import cm",
                           "from mpl_toolkits.mplot3d.axes3d import get_test_data"],
        var_declare_statements=["fig = plt.figure(figsize=plt.figaspect(0.5))",
                                "ax = fig.add_subplot(1, 2, 2, projection='3d')",
                                "X, Y, Z = get_test_data(0.05)",
                                "pl1 = ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)"],
        var_modify_statements=["pl1.set_linewidth(2.5)"]
    ),
    LibCoverageTestCase(
        module_name="networkx",
        class_name="networkx.classes.graph.Graph",
        var_name="G",
        import_statements=["import networkx as nx"],
        var_declare_statements=["G = nx.Graph()"],
        var_modify_statements=["G.add_node(1)"]
    ),
    LibCoverageTestCase(
        module_name="networkx",
        class_name="networkx.classes.digraph.DiGraph",
        var_name="DG",
        import_statements=["import networkx as nx"],
        var_declare_statements=["DG = nx.DiGraph()"],
        var_modify_statements=["DG.add_edge(2, 1)"]
    ),
    LibCoverageTestCase(
        module_name="nltk",
        class_name="nltk.stem.porter.PorterStemmer",
        var_name="stemmer",
        import_statements=["from nltk.stem.porter import *"],
        var_declare_statements=["stemmer = PorterStemmer()"],
        var_modify_statements=["stemmer.mode='MARTIN_EXTENSIONS'"]
    )
]
