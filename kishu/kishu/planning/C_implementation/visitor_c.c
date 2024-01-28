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
const int TYPE_BYTE = 7;
const int TYPE_BYTEARR = 8;





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
        else if (PyAnySet_Check(obj)) {
            visitor -> visit_set(obj, visitor -> visited, include_id, state);
            PyObject *iter = PyObject_GetIter(obj);
            PyObject *item;
            while ((item = PyIter_Next(iter))) {
                get_object_state(item, visitor, include_id, state);
            }
            return state;     
        }
        else if (PyDict_Check(obj)) {
            visitor -> visit_dict(obj, visitor -> visited, include_id, state);
            PyObject *keys = PyDict_Keys(obj);
            PyObject *values = PyDict_Values(obj);
            Py_ssize_t size = PyList_Size(keys);
            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *key = PyList_GetItem(keys, i);
                PyObject *value = PyList_GetItem(values, i);

                // process key
                get_object_state(key, visitor, include_id, state);

                // process values
                get_object_state(value, visitor, include_id, state);
            }
            return state;        
        }
        else if (PyBytes_Check(obj) || PyByteArray_Check(obj)) {
            return visitor -> visit_byte(obj, visitor -> visited, include_id, state);
        }
        else if(PyType_Check(obj)) {
            return visitor -> visit_type(obj, visitor -> visited, include_id, state);
        }
        else if (PyCallable_Check(obj)) {
            return visitor -> visit_callable(obj, visitor -> visited, include_id, state);
        }
        else if (PyObject_HasAttrString(obj, "__reduce_ex__")) {
            visitor -> visit_custom_obj(obj, visitor -> visited, include_id, state);
            if (is_pickable(obj)) {
                // Prepare the argument for __reduce_ex__
                PyObject *arg = PyLong_FromLong(4);
                if (!arg) {
                    // Handle error in creating the argument
                    return NULL;
                }

                // Call __reduce_ex__(4)
                PyObject *reduced = PyObject_CallMethod(obj, "__reduce_ex__", "(O)", arg);
                Py_DECREF(arg); // Decrement the reference count for arg

                if (!is_pandas_RangeIndex_instance(obj))
                    visitor -> update_state_id(obj, state);
                
                if (PyUnicode_Check(obj))
                    return visitor -> visit_primitive(reduced, state);

                Py_ssize_t size = PyTuple_Size(reduced);
                for (Py_ssize_t i = 1; i < size; i++) {
                    PyObject *item = PyTuple_GetItem(reduced, i);
                    get_object_state(item, visitor, 0, state);
                }
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
    if ( (obj == Py_None) || (obj == Py_NotImplemented) || (obj == Py_Ellipsis) || PyLong_Check(obj) || PyFloat_Check(obj) || PyBool_Check(obj) || PyUnicode_Check(obj))
        return 1;
    else
        return 0;
}

int is_pickable(PyObject *obj) {
    static PyObject *dumps_func = NULL;

    // Import pickle and get dumps function only once
    if (dumps_func == NULL) {
        PyObject *pickle_module = PyImport_ImportModule("pickle");
        if (!pickle_module) {
            // Handle error: unable to import pickle
            return 0; // Considered not picklable
        }

        dumps_func = PyObject_GetAttrString(pickle_module, "dumps");
        Py_DECREF(pickle_module); // Done with pickle module
        if (!dumps_func) {
            // Handle error: dumps function not found
            return 0; // Considered not picklable
        }
    }

    // Try to pickle the object
    PyObject *args = PyTuple_Pack(1, obj);
    if(!args) {
        return 0;
    }

    PyObject *result = PyObject_CallObject(dumps_func, args);
    Py_DECREF(args); // Decrement reference count for args

    if (!result) {
        // An exception occurred, clear it and consider the object not picklable
        PyErr_Clear();
        return 0; // False
    }

    // The object is picklable
    Py_DECREF(result); // Decrement reference count for result
    return 1; // True
}

int is_pickable_using_Python(PyObject *obj) {
    PyObject *pModule, *pFunc, *pArgs, *pValue;

    pModule = PyImport_ImportModule("test_is_pickable");
    if (!pModule) {
        PyErr_Print();
        fprintf(stderr, "Failed to load");
        return -1;
    }

    pFunc = PyObject_GetAttrString(pModule, "is_pickable");
    if (!pFunc || !PyCallable_Check(pFunc)) {
        if (PyErr_Occurred())
            PyErr_Print();
        fprintf(stderr, "Cannot find function");
        Py_DECREF(pModule);
        return -1;
    }

    pArgs = PyTuple_New(1);
    PyTuple_SetItem(pArgs, 0, obj);
    Py_INCREF(obj);

    pValue = PyObject_CallObject(pFunc, pArgs);
    Py_DECREF(pArgs);
    Py_DECREF(pFunc);

    long long temp_obj;

    if (pValue != NULL) {
        // printf("Function call succeeded.\n");
        temp_obj = PyLong_AsLongLong(pValue);
        Py_DECREF(pValue);
    } else {
        PyErr_Print();
        fprintf(stderr, "Call failed.\n");
        Py_DECREF(pModule);
        return -1;
    }

    Py_DECREF(pModule);
    return temp_obj;
}

int is_pandas_RangeIndex_instance(PyObject *obj) {
    static PyObject *RangeIndex = NULL;

    if (RangeIndex == NULL) {
        // Import the pandas.core.indexes.range module and get RangeIndex
        PyObject *pandas_module = PyImport_ImportModule("pandas.core.indexes.range");
        if (!pandas_module) {
            // Handle error
            return 0;
        }

        RangeIndex = PyObject_GetAttrString(pandas_module, "RangeIndex");
        Py_DECREF(pandas_module);
        if (!RangeIndex) {
            // Handle error
            return 0;
        }
    }

    // Call the recursive function
    if (PyObject_IsInstance(obj, RangeIndex))
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