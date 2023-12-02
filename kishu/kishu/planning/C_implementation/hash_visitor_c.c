#include <Python.h>
#include "hash_visitor_c.h"
#include "xxhash.h"


VisitorReturnType* hash_has_visited(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {
    // Implementation specific to HashVisitor

    Visited* current = visited;
    while(current != NULL) {
        if (current ->pyObject == obj)
            return state;
    }
    return NULL;
}

// Handles int, float, bool, str, None, NotImplemented, Ellipsis
VisitorReturnType* hash_visit_primitive(PyObject *obj, VisitorReturnType* state) {
    if (obj == Py_None) {
        /* Python - None */
        static const int none_value = 0;
        XXH32_update(state -> hashed_state, &TYPE_NONE, sizeof(TYPE_NONE));
        XXH32_update(state -> hashed_state, &none_value, sizeof(none_value));
    } else if (obj == Py_NotImplemented) {
        /* Python - NotImplemented */
        static const int notimplemented_value = 1;
        XXH32_update(state -> hashed_state, &TYPE_NOTIMPLEMENTED, sizeof(TYPE_NOTIMPLEMENTED));
        XXH32_update(state -> hashed_state, &notimplemented_value, sizeof(notimplemented_value));
    } else if (obj == Py_Ellipsis) {
        /* Python - Ellipsis */
        static const int ellipsis_value = 2;
        XXH32_update(state -> hashed_state, &TYPE_ELLIPSIS, sizeof(TYPE_ELLIPSIS));
        XXH32_update(state -> hashed_state, &ellipsis_value, sizeof(ellipsis_value)); 
    } else if (PyLong_Check(obj)) {
        /* Python - int */
        long long value = PyLong_AsLongLong(obj);
        XXH32_update(state -> hashed_state, &TYPE_INT, sizeof(TYPE_INT));
        XXH32_update(state -> hashed_state, &value, sizeof(value));
    } else if (PyFloat_Check(obj)) {
        /* Python - float */
        double value = PyFloat_AsDouble(obj);
        XXH32_update(state -> hashed_state, &TYPE_FLOAT, sizeof(TYPE_FLOAT));
        XXH32_update(state -> hashed_state, &value, sizeof(value));
    } else if (PyBool_Check(obj)) {
        /* Python - bool */
        long value = PyObject_IsTrue(obj);
        XXH32_update(state -> hashed_state, &TYPE_BOOL, sizeof(TYPE_BOOL));
        XXH32_update(state -> hashed_state, &value, sizeof(value));
    } else if (PyUnicode_Check(obj)) {
        /* Python - str */
        Py_ssize_t length;
        const char* data = PyUnicode_AsUTF8AndSize(obj, &length);
        XXH32_update(state -> hashed_state, &TYPE_STR, sizeof(TYPE_STR));
        XXH32_update(state -> hashed_state, data, (size_t)length);
    }  else {
        // Set TypeError for unknown primitive type
        PyErr_SetString(PyExc_TypeError, "Unsupported object type for hashing");
        XXH32_freeState(state -> hashed_state);
        return NULL;
    }

    // VisitorReturnType result;
    // result.hashed_state = state -> hashed_state;

    return state;
}

VisitorReturnType* hash_visit_tuple(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}
VisitorReturnType* hash_visit_list(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}
VisitorReturnType* hash_visit_set(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}
VisitorReturnType* hash_visit_dict(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}
VisitorReturnType* hash_visit_byte(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}
VisitorReturnType* hash_visit_type(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}
VisitorReturnType* hash_visit_callable(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}
VisitorReturnType* hash_visit_custom_obj(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}
VisitorReturnType* hash_visit_other(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state) {return NULL;}



Visitor* create_hash_visitor() {
    int seed = 0;
    /* Initialze hash visitor */
    Visitor* visitor = (Visitor*)malloc(sizeof(Visitor));
    // VisitorReturnType* state = (VisitorReturnType*)malloc(sizeof(VisitorReturnType*));
    /* Initialize hash visitor functions */
    visitor->has_visited = hash_has_visited;
    visitor->visit_primitive = hash_visit_primitive;
    visitor->visit_tuple = hash_visit_tuple;
    visitor->visit_list = hash_visit_list;
    visitor->visit_set = hash_visit_set;
    visitor->visit_dict = hash_visit_dict;
    visitor->visit_byte = hash_visit_byte;
    visitor->visit_type = hash_visit_type;
    visitor->visit_callable = hash_visit_callable;
    visitor->visit_custom_obj = hash_visit_custom_obj;
    visitor->visit_other = hash_visit_other;

    visitor->visited = NULL;

    XXH32_state_t* xxhash_state = XXH32_createState();
    XXH32_reset(xxhash_state, seed);

    VisitorReturnType* state = (VisitorReturnType*)malloc(sizeof(VisitorReturnType*));
    state -> hashed_state = xxhash_state;

    /* Initialize hash visitor state */
    visitor -> state = state;
    
    return visitor;
}