#include <Python.h>
#include "visitor_c.h"
#include "hash_visitor_c.h"

// Definitions of global type identifiers
const int TYPE_NONE = 0;
const int TYPE_NOTIMPLEMENTED = 1;
const int TYPE_ELLIPSIS = 2;
const int TYPE_INT = 3;
const int TYPE_FLOAT = 4;
const int TYPE_BOOL = 5;
const int TYPE_STR = 6;





VisitorReturnType* get_object_hash(PyObject *obj) {
    Visitor* hash_visitor = create_hash_visitor();
    return get_object_state(obj, hash_visitor, 1, hash_visitor -> state);
}

VisitorReturnType* get_object_state(PyObject *obj, Visitor *visitor, int include_id, VisitorReturnType* state) {
    VisitorReturnType* ret_state;
    if (NULL != (ret_state = (visitor -> has_visited(obj, visitor -> visited, include_id, state))))
        return ret_state;
    else {
        /* Not been visited yet */
        if (is_primitive(obj))
            return visitor -> visit_primitive(obj, state);
        else if (PyTuple_Check(obj)) {
            visitor -> visit_tuple(obj, visitor -> visited, include_id, state);
            Py_ssize_t size = PyTuple_Size(obj);
            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *item = PyTuple_GetItem(obj, i);
                get_object_state(item, visitor, include_id, state);
            }
            return state;
        }
        else if (PyList_Check(obj)) {
            visitor -> visit_list(obj, visitor -> visited, include_id, state);
            Py_ssize_t size = PyList_Size(obj);
            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *item = PyList_GetItem(obj, i);
                get_object_state(item, visitor, include_id, state);
            } 
            return state;            
        }
        else {
            PyErr_SetString(PyExc_TypeError, "Unsupported object type for ObjectStare");
            return NULL;
        }
    } 
}

int is_primitive(PyObject *obj) {
    if ( (obj == Py_None) || (obj == Py_NotImplemented) || (obj == Py_Ellipsis) || PyLong_Check(obj) || PyFloat_Check(obj) || PyBool_Check(obj) || PyUnicode_Check(obj) )
        return 1;
    else
        return 0;
}

static PyObject* get_object_hash_wrapper(PyObject* self, PyObject* args) {
    // Parse arguments from Python to C
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    // Calling get_object_hash
    VisitorReturnType* result = get_object_hash(obj);

    // Convert the result to a PyCapsule
    PyObject* state_capsule = PyCapsule_New(result, "XXH32_hash", NULL);

    if (state_capsule == NULL)
        return NULL;
    
    return state_capsule;
}

static PyObject *get_digest_hash_wrapper(PyObject *self, PyObject *args) {
    if (self == NULL) {
        return NULL;
    }

    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }
    VisitorReturnType* result = (VisitorReturnType *)PyCapsule_GetPointer(obj, "XXH32_hash");

    if (result == NULL)
        return NULL;

    unsigned int digest_hash = XXH32_digest(result -> hashed_state);

    return PyLong_FromUnsignedLong(digest_hash);
}

static PyMethodDef VisitorMethods[] = {
    {"get_object_hash_wrapper", get_object_hash_wrapper, METH_VARARGS,
     "Python interface for the get_object_hash C library function."},
    {"get_digest_hash_wrapper", get_digest_hash_wrapper, METH_VARARGS,
     "Python interface for the get_digest_hash_wrapper C library function."},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef VisitorModule = {
    PyModuleDef_HEAD_INIT,
    "VisitorModule", // name of the module
    "Module documentation", // module documentation
    -1,       // size of per-interpreter state of the module, or -1 if the module keeps state in global variables.
    VisitorMethods
};

PyMODINIT_FUNC PyInit_VisitorModule(void) {
    return PyModule_Create(&VisitorModule);
}