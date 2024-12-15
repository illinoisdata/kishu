Limitations
=====

Kishu may fail to correctly checkpoint notebook sessions containing the following items:

Silent Pickling Errors
-----
Kishu relies on the assumption that any object, when pickled then unpickled, is identical to the original object, and does not automatically detect cases where this assumption is violated (i.e., silent pickling errors). This is typically caused by errors in the object class' `__reduce__` function:

