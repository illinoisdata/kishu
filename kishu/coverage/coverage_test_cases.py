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
        module_name="xgboost",
        class_name="xgboost.XGBRegressor",
        var_name="model",
        import_statements=[
            "import numpy as np",
            "import xgboost"
        ],
        var_declare_statements=[
            "X_train = np.random.rand(100, 10)",
            "y_train = np.random.rand(100)",
            "model = xgboost.XGBRegressor()",
            "model.fit(X_train, y_train)"
        ],
        var_modify_statements=[
            "model.learning_rate = 0.1",
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
        var_declare_statements=["x = np.linspace(0.1, 2 * np.pi, 41)",
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
        var_declare_statements=["xcenter, ycenter = 0.38, 0.52",
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
        var_declare_statements=["x_tail, y_tail = 0.1, 0.5",
                                "x_head, y_head = 0.9, 0.8",
                                "arrow = mpatches.FancyArrowPatch((x_tail, y_tail), (x_head, y_head),mutation_scale=100)"],
        var_modify_statements=["arrow.set_linewidth(2.0)"]
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
    )
]
