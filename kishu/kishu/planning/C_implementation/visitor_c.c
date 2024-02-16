#include <Python.h>
#include "visitor_c.h"
#include "hash_visitor_c.h"
#include <stdbool.h>

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

// VisitorReturnType* get_object_hash(PyObject *obj) {
//     Visitor* hash_visitor = create_hash_visitor();
//     return get_object_state(obj, hash_visitor, 1, hash_visitor -> state);
// }

Visitor* get_object_hash(PyObject *obj) {
    Visitor* hash_visitor = create_hash_visitor();
    get_object_state(obj, hash_visitor, true, hash_visitor->state);
    return hash_visitor;
}

VisitorReturnType* get_object_state(PyObject *obj, Visitor *visitor, const bool include_id, VisitorReturnType* state) {
    VisitorReturnType* ret_state;
    if (NULL != (ret_state = (visitor->has_visited(obj, visitor->visited, include_id, state))))
        return visitor->handle_visited(obj, include_id, state, visitor->list_included);
    else {
        /* Not been visited yet */
        if (is_primitive(obj))
            return visitor->visit_primitive(obj, state, visitor->list_included);
        else if (PyTuple_Check(obj)) {
            /* Tuple */
            visitor->visit_tuple(obj, &(visitor->visited), include_id, state, visitor->list_included);
            Py_ssize_t size = PyTuple_Size(obj);
            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *item = PyTuple_GetItem(obj, i);
                if (!get_object_state(item, visitor, include_id, state)) {
                    // Error
                    return NULL;
                }
            }
            return state;
        }
        else if (PyList_Check(obj)) {
            /* List */
            visitor->visit_list(obj, &(visitor->visited), include_id, state, visitor->list_included);
            Py_ssize_t size = PyList_Size(obj);
            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *item = PyList_GetItem(obj, i);
                if (!get_object_state(item, visitor, include_id, state)) {
                    // Error
                    return NULL;
                }
            } 
            return state;            
        }
        else if (PyAnySet_Check(obj)) {
            /* Set */
            visitor->visit_set(obj, &(visitor->visited), include_id, state, visitor->list_included);
            PyObject *iter = PyObject_GetIter(obj);
            PyObject *item;
            while ((item = PyIter_Next(iter))) {
                if (!get_object_state(item, visitor, include_id, state)) {
                    // Error
                    return NULL;
                }
            }
            return state;     
        }
        else if (PyDict_Check(obj)) {
            /* Dictionary */
            visitor->visit_dict(obj, &(visitor->visited), include_id, state, visitor->list_included);
            PyObject *keys = PyDict_Keys(obj);
            PyObject *values = PyDict_Values(obj);
            Py_ssize_t size = PyList_Size(keys);
            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *key = PyList_GetItem(keys, i);
                PyObject *value = PyList_GetItem(values, i);

                // process key
                if (!get_object_state(key, visitor, include_id, state)) {
                    return NULL;
                }

                // process values
                if (!get_object_state(value, visitor, include_id, state)) {
                    // Error
                    return NULL;
                }
            }
            return state;        
        }
        else if (PyBytes_Check(obj) || PyByteArray_Check(obj)) {
            /* Byte or Bytearray */
            return visitor->visit_byte(obj, &(visitor->visited), include_id, state, visitor->list_included);
        }
        else if(PyType_Check(obj)) {
            /* type */
            return visitor->visit_type(obj, &(visitor->visited), include_id, state, visitor->list_included);
        }
        else if (PyCallable_Check(obj)) {
            /* Callable object */
            return visitor->visit_callable(obj, &(visitor->visited), include_id, state, visitor->list_included);
        }
        else if (PyObject_HasAttrString(obj, "__reduce_ex__")) {
            /* Custom object */
            visitor->visit_custom_obj(obj, &(visitor->visited), include_id, state, visitor->list_included);
            int picklable = is_picklable(obj);
            if (picklable == -1)
                return NULL;

            if (picklable) {
                // Prepare the argument for __reduce_ex__
                PyObject *arg = PyLong_FromLong(4);
                if (!arg) {
                    // Handle error in creating the argument
                    return NULL;
                }

                // Call __reduce_ex__(4)
                PyObject *reduced = PyObject_CallMethod(obj, "__reduce_ex__", "(O)", arg);
                Py_DECREF(arg); // Decrement the reference count for arg

                if (!reduced)
                    return state;

                int range_index_instance = is_pandas_RangeIndex_instance(obj);
                if (range_index_instance == -1)
                    return NULL;

                if (!range_index_instance)
                    visitor->update_state_id(obj, state, visitor->list_included);
                
                if (PyUnicode_Check(reduced))
                    return visitor->visit_primitive(reduced, state, visitor->list_included);

                // Uncomment the below code if pickle check is removed in python file
                // int plt_callback_instance = is_plt_Callback_instance(obj);
                // if (plt_callback_instance == -1)
                //     return NULL;
                
                // if (plt_callback_instance) 
                //     return state;

                Py_ssize_t size = PyTuple_Size(reduced);
                for (Py_ssize_t i = 1; i < size; i++) {
                    PyObject *item = PyTuple_GetItem(reduced, i);
                    if (!get_object_state(item, visitor, false, state)) {
                        // Error
                        return NULL;
                    }
                }
            }
            return state;
        }
        else {
            /* Not supported yet */
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

int is_picklable(PyObject *obj) {
    static PyObject *dumps_func = NULL;

    // Import pickle and get dumps function only once
    if (dumps_func == NULL) {
        PyObject *pickle_module = PyImport_ImportModule("pickle");
        if (!pickle_module) {
            // Handle error: unable to import pickle
            PyErr_Print();
            return -1; // Considered not picklable
        }

        dumps_func = PyObject_GetAttrString(pickle_module, "dumps");
        Py_DECREF(pickle_module); // Done with pickle module
        if (!dumps_func) {
            // Handle error: dumps function not found
            PyErr_Print();
            return -1; // Considered not picklable
        }
    }

    // Prepare args
    PyObject *args = PyTuple_Pack(1, obj);
    if(!args) {
        // Failed to create tuple
        return -1;
    }

    // Try to pickle the object
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

/* Uncomment below code if pickle check is removed in python file*/
// int is_plt_Callback_instance(PyObject *obj) {
//     static PyObject *CallbackRegistry = NULL;

//     if (CallbackRegistry == NULL) {
//         PyObject *plt_module = PyImport_ImportModule("matplotlib.cbook");
//         if (!plt_module) {
//             // Handle error
//             PyErr_Print();
//             return -1;
//         }

//         CallbackRegistry = PyObject_GetAttrString(plt_module, "CallbackRegistry");
//         Py_DECREF(plt_module);
//         if (!CallbackRegistry) {
//             // Handle error
//             PyErr_Print();
//             return -1;
//         }    
//     }

//     if (PyObject_IsInstance(obj, CallbackRegistry))
//         return 1;
//     else
//         return 0;
// }

int is_pandas_RangeIndex_instance(PyObject *obj) {
    static PyObject *RangeIndex = NULL;



    if (RangeIndex == NULL) {
        // Import the pandas.core.indexes.range module and get RangeIndex
        PyObject *pandas_module = PyImport_ImportModule("pandas.core.indexes.range");
        if (!pandas_module) {
            // Handle error
            PyErr_Print();
            return -1;
        }

        RangeIndex = PyObject_GetAttrString(pandas_module, "RangeIndex");
        Py_DECREF(pandas_module);
        if (!RangeIndex) {
            // Handle error
            PyErr_Print();
            return -1;
        }
    }

    if (PyObject_IsInstance(obj, RangeIndex))
        return 1;
    else
        return 0;
}

/*
* Python interface function to get visitor object.
* args: - Python object to hash
*/
static PyObject* get_visitor_wrapper(PyObject* self, PyObject* args) {
    // Parse arguments from Python to C
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    // Calling get_object_hash
    // VisitorReturnType* result = get_object_hash(obj);
    Visitor* hash_visitor = get_object_hash(obj);

    // Convert the result to a PyCapsule
    // PyObject* state_capsule = PyCapsule_New(result, "XXH32_hash", NULL);
    PyObject* state_capsule = PyCapsule_New(hash_visitor, "Visitor_hash", NULL);

    if (state_capsule == NULL)
        return NULL;
    
    return state_capsule;
}

/*
* Python interface function to get hashed state from Visitor Object
* args: Visitor object
*/
static PyObject *get_digest_hash_wrapper(PyObject *self, PyObject *args) {
    if (self == NULL) {
        return NULL;
    }

    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }
    // VisitorReturnType* result = (VisitorReturnType *)PyCapsule_GetPointer(obj, "XXH32_hash");
    Visitor* hash_visitor = (Visitor *)PyCapsule_GetPointer(obj, "Visitor_hash");

    if (hash_visitor == NULL)
        return NULL;

    unsigned long digest_hash = XXH3_64bits_digest(hash_visitor->state->hashed_state);

    return PyLong_FromUnsignedLong(digest_hash);
}

/*
* Python interface funtion to get hashed state of object
* args: object whose state needs to be hashed
*/
static PyObject *get_object_hash_wrapper(PyObject *self, PyObject *args) {
    // Parse arguments from Python to C
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    // Calling get_object_hash
    // VisitorReturnType* result = get_object_hash(obj); 
    Visitor* hash_visitor = get_object_hash(obj);    
    unsigned long digest_hash = XXH3_64bits_digest(hash_visitor->state->hashed_state);

    return PyLong_FromUnsignedLong(digest_hash);
}

/*
* Python interface funtion to get hashed state of object and items hashed during traversing
* args: object whose state needs to be hashed
* Return: Tuple(hashed state, traversed items)
*/
static PyObject *get_object_hash_and_trav_wrapper(PyObject *self, PyObject *args) {
    // Parse arguments from Python to C
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    Visitor* hash_visitor = get_object_hash(obj);    

    unsigned long digest_hash = XXH3_64bits_digest(hash_visitor->state->hashed_state);

    return PyTuple_Pack(2, PyLong_FromUnsignedLong(digest_hash), hash_visitor->list_included);
}

/*
* Python interface funtion to get items hashed during traversing
* args: Visitor object
*/
static PyObject *get_visited_objs_wrapper(PyObject *self, PyObject *args) {
    // Parse arguments from Python to C
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    Visitor* hash_visitor = (Visitor *)PyCapsule_GetPointer(obj, "Visitor_hash");

    return hash_visitor->list_included;
}

static PyMethodDef VisitorMethods[] = {
    {"get_object_hash_and_trav_wrapper", get_object_hash_and_trav_wrapper, METH_VARARGS,
     "Python interface to get hashed state and traversal as a tuple"},
    {"get_visitor_wrapper", get_visitor_wrapper, METH_VARARGS,
     "Python interface to get xxhash object"},
    {"get_digest_hash_wrapper", get_digest_hash_wrapper, METH_VARARGS,
     "Python interface to get hash value from xxhash object"},
    {"get_object_hash_wrapper", get_object_hash_wrapper, METH_VARARGS,
     "Python interface for getting hashed object state of object"}, 
    {"get_visited_objs_wrapper", get_visited_objs_wrapper, METH_VARARGS,
     "Python interface for the visited objs."},     
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