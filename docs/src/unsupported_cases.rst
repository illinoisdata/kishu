Limitations
=====

Kishu may fail to correctly checkpoint notebook sessions containing the following items:

Silent Pickling Errors
-----
Kishu relies on the assumption that any object, when pickled then unpickled, is identical to the original object, and does not automatically detect cases where this assumption is violated (i.e., silent pickling errors). This is typically caused by errors in the object class' `reduce`_ function which acts as its pickling instructions; for example, an object with the below reduction (incorrectly) returns an empty (byte)string when pickled.

.. _reduce: https://docs.python.org/3/library/pickle.html

.. code-block:: console

  def \_\_reduce\_\_(self):
      return ""


As a potential workaround, you can add object classes with incorrect reductions to a `blocklist`_ in Kishu's config to inform it to never try to store (and always recompute) objects belonging to these classes.

.. _blocklist: https://github.com/illinoisdata/kishu/blob/main/docs/src/usage.rst

Non-Deterministic and Unpicklable Objects
-----
Kishu relies on cell replay to reconstruct unpicklable objects (e.g., generators). However, if the unpicklable object itself is created through non-deterministic means, Kishu will fail to exactly recreate it on undo/checkout, for example (assuming the seed for `random` was not set):

.. code-block:: console

  nondet_gen = (i for i in range(random.randint(5, 10)))
