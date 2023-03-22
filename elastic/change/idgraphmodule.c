#define PY_SSIZE_T_CLEAN
#include <Python.h>

static void 
idgraph_create(PyObject *self, PyObject *args){

    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj))
        return NULL;
    if (obj != NULL)
    {
        printf("Found an object\n");
    }

    // dict, list, tuple, set

    if (PyUnicode_Check(obj)) {
        printf("Object is a string: %s\n", PyUnicode_AsUTF8(obj));
    } else if (PyList_Check(obj)) {
        printf("Object is a list\n");
        // Process the list
    } else if (PyDict_Check(obj)) {
        printf("Object is a dictionary\n");
        // Process the dictionary
    } else if (PyTuple_Check(obj)){
        printf("Tuple object type\n");
    } else if (PySet_Check(obj)){
        printf("Set object type\n");
    }
    Py_RETURN_NONE;
    
}

static PyMethodDef IdGraphMethods[] = {
    {"idgraph", idgraph_create, METH_VARARGS, "Python interface for the idgraph C library function"},
    {NULL, NULL, 0, NULL}
};


static struct PyModuleDef idgrapgmodule = {
    PyModuleDef_HEAD_INIT,
    "idgraph",
    "Python interface for the idgraph C library function",
    -1,
    IdGraphMethods
};

PyMODINIT_FUNC PyInit_idgraph(void) {
    return PyModule_Create(&idgrapgmodule);
}