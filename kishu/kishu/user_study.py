import time
import numpy as np
import pandas as pd
from sklearn import metrics
from termcolor import cprint

X_test = pd.DataFrame({
    'longitude': [-121.46, -117.23, -119.04, -117.13, -118.70],
    'housing_median_age': [29, 7, 44, 24, 27],
    'total_bedrooms': [226.0, 710.0, 1007.0, 331.0, 324.0],
    'population': [2237, 2015, 667, 898, 1837],
    'median_income': [2.1736, 6.3373, 2.8750, 2.2264, 4.4964]
})
Y_test = pd.DataFrame({
    'median_house_value': [72100, 279600, 82700, 112500, 238300]
})

def submit_cell_execution(info) -> None:
    success = False
    try:
        if "read_csv" in info.raw_cell:
            time.sleep(50)
        if "fit" in info.raw_cell:
            time.sleep(40)
        else:
            time.sleep(min(len(info.raw_cell.split("\n")), 10))
        # print(ts)
        success = True
    except KeyboardInterrupt:
        cprint(f"KeyboardInterrupt while submitting cell execution.", "light_red", attrs=["underline", "bold"])
    if not success:
        raise KeyboardInterrupt("Cancelled cell execution")

def install_submit_cell_execution() -> None:
    try:
        ip = eval('get_ipython()')
        ip.events.register('pre_run_cell', submit_cell_execution)
    except Exception:
        pass

def check_train_test_dataset(X_train, Y_train, X_test, Y_test):
    expected_rows = 16512 + 4128
    if X_train.shape[0] + X_test.shape[0] != expected_rows:
        cprint(f"CHECK FAILED: Rows in variable `housing` have been dropped accidentally. Find when `housing` has fewer than {expected_rows} rows", "light_red", attrs=["underline", "bold"])
        return False
    if Y_train.shape[0] + Y_test.shape[0] != expected_rows:
        cprint(f"CHECK FAILED: Rows in variable `housing` have been dropped accidentally. Find when `housing` has fewer than {expected_rows} rows", "light_red", attrs=["underline", "bold"])
        return False
    null_cols = X_train.columns[X_train.isnull().any()].tolist()
    if len(null_cols) > 0:
        cprint(f"CHECK FAILED: `X_train` contains a missing value {null_cols}", "light_red", attrs=["underline", "bold"])
        cprint(f"Hint: Imputation should have replaced these missing values", "light_red", attrs=["underline", "bold"])
        return False
    null_cols = X_test.columns[X_test.isnull().any()].tolist()
    if len(null_cols) > 0:
        cprint(f"CHECK FAILED: `X_test` contains a missing value {null_cols}", "light_red", attrs=["underline", "bold"])
        cprint(f"Hint: Imputation should have replaced these missing values", "light_red", attrs=["underline", "bold"])
        return False
    cprint("CHECK PASSED", "light_green", attrs=["underline", "bold"])
    return True

def submit(model):
    try:
        Y_pred = model.predict(X_test)
        rmse = np.sqrt(metrics.mean_squared_error(Y_test, Y_pred))
        cprint(f"CHECK PASSED (RMSE={rmse})", "light_green", attrs=["underline", "bold"])
        return True
    except Exception as e:
        cprint(f"{type(e).__name__}: {e}", "light_red", attrs=["bold"])
        cprint("CHECK FAILED", "light_red", attrs=["underline", "bold"])
        if "income_cat" in str(e):
            cprint(f"Hint: The model was trained with a temporary column (\"income_cat\").", "light_red", attrs=["underline", "bold"])
        return False
