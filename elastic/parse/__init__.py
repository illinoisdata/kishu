"""
Extracts accessed variables in Python scripts.
"""

from parse.var import Var


def identify_vars(code_block: str) -> list[Var]:
    """
    Given a code block (see examples below), identify all the variables appearing in it.

    # Example Code Blocks

    ## Example 1:

    ```
    a = 1
    b = 3
    c = a + b
    ```

    set([a, b, c]) must be identified.


    ## Example 2:

    ```
    import numpy as np

    a = np.zeros((2,2))
    b = a + 1
    ```

    set([np, a, b]) must be identified.


    ## Example 3:

    ```
    def foo(item):
        mylist.append(item)     # accessing a global variable "mylist"
    item = 3
    foo(item)
    ```

    set([mylist, item]) must be identified. If "item = 3" is inlined and foo(3) is called without
    creating the "item" variable, "item" won't be included in the identified set.

    We inspect the definition of the "foo" because it is a function defined in the global scope,
    not in any module/package. (We consider all the functions listed in dir() as the global-scope
    functions. We won't allow the from-import pattern, preventing dir() from including the functions
    defined inside modules.)


    ## Example 4:

    ```
    def goo(item):
        mylist2.append(item)     # accessing a global variable "mylist2"

    def foo(item):
        mylist.append(item)     # accessing a global variable "mylist"
        goo(item)

    foo(3)
    ```

    set([mylist, mylist2]) must be identified. 


    ## Example 5:

    ```
    def foo(item):
        if random.random() < 0.5:
            mylist.append(item)     # accessing a global variable "mylist"
            return
        foo(item)

    foo(3)
    ```

    set([mylist]) must be identified. The "foo" function appears again inside the function itself,
    which must not result in an infinite loop during our analysis.


    # Future Goals

    1. We want to distinguish regular variables and modules.

    2. We want to identify *related* variables, where related variables mean the variables sharing
    references (to other objects). For example, two variables --- a and b --- created as follows 
    `a = [c] and b = [c]` are related because they share the reference to the same object (c).

    3. We will identify the "from module import *" pattern.
    """
    pass

