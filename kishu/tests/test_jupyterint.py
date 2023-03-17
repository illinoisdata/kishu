from IPython import get_ipython
from kishu.jupyterint import _append_kishu_capture
from kishu.jupyterint import _is_kishu_function


def test_is_kishu_function():
    assert _is_kishu_function(_append_kishu_capture) == True

    # Any other functions will be evaluated to be false
    assert _is_kishu_function(get_ipython) == False

    # Non functions will be evaluated to be false
    assert _is_kishu_function(1) == False

