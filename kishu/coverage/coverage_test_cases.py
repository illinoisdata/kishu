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
        module_name="sklearn",
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
        module_name="sklearn",
        class_name="sklearn.cluster",
        var_name="kmeans",
        import_statements=["import numpy as np", "from sklearn.cluster import MiniBatchKMeans"],
        var_declare_statements=[
            "X = np.array([[1, 2], [1, 4], [1, 0],
                  [4, 2], [4, 0], [4, 4],
                  [4, 5], [0, 1], [2, 2],
                  [3, 2], [5, 5], [1, -1]])",
            "kmeans = MiniBatchKMeans(n_clusters = 2, random_state = 0, batch_size=6, n_init='auto')",
            "kmeans = kmeans.partial_fit(X[0:6,:])"
        ],
        var_modify_statements=["kmeans.batch_size=4"]
    ),
    LibCoverageTestCase(
        module_name="sklearn",
        class_name="sklearn.datasets",
        var_name="data",
        import_statements=["from sklearn.datasets import fetch_california_housing"],
        var_declare_statements=[
            "data = fetch_california_housing()"
        ],
        var_modify_statements=["data.data[0,0] = 15"]
    ),
    LibCoverageTestCase(
        module_name="sklearn",
        class_name="sklearn.datasets",
        var_name="X",
        import_statements=["from sklearn.datasets import make_friedman1"],
        var_declare_statements=[
            "X, y = make_friedman1(random_state=42)"
        ],
        var_modify_statements=["X[3,2] = 10"]
    ),
    LibCoverageTestCase(
        module_name="sklearn",
        class_name="sklearn.decomposition",
        var_name="transformer",
        import_statements=[
            "from sklearn.datasets import load_digits", 
            "from sklearn.decomposition import IncrementalPCA"
        ],
        var_declare_statements=[
            "X, _ = load_digits(return_X_y=True)"
            "transformer = IncrementalPCA(n_components=7, batch_size=200)"
        ],
        var_modify_statements=["transformer.batch_size = 201", "transformer.n_components=8"]
    ),
    LibCoverageTestCase(
        module_name="sklearn",
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
        module_name="sklearn",
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
        module_name="sklearn",
        class_name="sklearn.ensemble",
        var_name="clf",
        import_statements=[
            "from sklearn.ensemble import AdaBoostClassifier",
            "from sklearn.datasets import make_classification"
        ],
        var_declare_statements=[
            "X, y = make_classification(n_samples=1000, n_features=4,
                           n_informative=2, n_redundant=0,
                           random_state=0, shuffle=False)",
            "X1, y1 = make_classification(n_samples=1000, n_features=4,
                           n_informative=2, n_redundant=0,
                           random_state=10, shuffle=False)",
            "clf = AdaBoostClassifier(n_estimators=100, algorithm='SAMME', random_state=42)",
            "clf.fit(X, y)"
        ],
        var_modify_statements=["clf.fit(X1, y1)"]
    ),
    LibCoverageTestCase(
        module_name="sklearn",
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
        module_name="sklearn",
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
        module_name="sklearn",
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
        module_name="sklearn",
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
            "current_dual_coefficients = kernel_ridge.dual_coef_",
            "new_dual_coefficients = np.full_like(current_dual_coefficients, fill_value=0.5)",
            "kernel_ridge.dual_coef_ = new_dual_coefficients"
        ]
    ),
    LibCoverageTestCase(
        module_name="sklearn",
        class_name="sklearn.linear_model",
        var_name="regression_model",
        import_statements=[
            "import numpy as np",
            "from sklearn.linear_model import LinearRegression"
        ],
        var_declare_statements=[
            "X = np.array([[1, 2], [3, 4], [5, 6]])",
            "y = np.array([1, 2, 3])",
            "regression_model = LinearRegression()"
            "regression_model.fit(X, y)",
        ],
        var_modify_statements=[
            "current_coefficients = regression_model.coef_",
            "new_coefficients = np.full_like(current_coefficients, fill_value=0.5)",
            "regression_model.coef_ = new_coefficients"
        ]
    ),
    LibCoverageTestCase(
        module_name="sklearn",
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
        module_name="sklearn",
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
        var_modify_statements=["sparse.tocsr()[1, 2] = 100"]
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
        ]
    ),


]   
