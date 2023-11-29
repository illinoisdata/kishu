#include <Python.h>
#include "hash_visitor_c.h"
#include "xxhash.h"


long* hash_check_visited(long *visited, long id, int include_id) {
    // Implementation specific to HashVisitor

    int* current = visited;
    while(current != NULL) {
        if (*current == id)
            return current;
    }
    return NULL;
}

// Handles int, float, bool, str, None, NotImplemented, Ellipsis
VisitorReturnType hash_visit_primitive(PyObject *obj, XXH32_state_t* hash_state) {
    if (obj == Py_None) {
        /* Python - None */
        static const int none_value = 0;
        XXH32_update(hash_state, &TYPE_NONE, sizeof(TYPE_NONE));
        XXH32_update(hash_state, &none_value, sizeof(none_value));
    } else if (obj == Py_NotImplemented) {
        /* Python - NotImplemented */
        static const int notimplemented_value = 1;
        XXH32_update(hash_state, &TYPE_NOTIMPLEMENTED, sizeof(TYPE_NOTIMPLEMENTED));
        XXH32_update(hash_state, &notimplemented_value, sizeof(notimplemented_value));
    } else if (obj == Py_Ellipsis) {
        /* Python - Ellipsis */
        static const int ellipsis_value = 2;
        XXH32_update(hash_state, &TYPE_ELLIPSIS, sizeof(TYPE_ELLIPSIS));
        XXH32_update(hash_state, &ellipsis_value, sizeof(ellipsis_value)); 
    } else if (PyLong_Check(obj)) {
        /* Python - int */
        long long value = PyLong_AsLongLong(obj);
        XXH32_update(hash_state, &TYPE_INT, sizeof(TYPE_INT));
        XXH32_update(hash_state, &value, sizeof(value));
    } else if (PyFloat_Check(obj)) {
        /* Python - float */
        double value = PyFloat_AsDouble(obj);
        XXH32_update(hash_state, &TYPE_FLOAT, sizeof(TYPE_FLOAT));
        XXH32_update(hash_state, &value, sizeof(value));
    } else if (PyBool_Check(obj)) {
        /* Python - bool */
        long value = PyObject_IsTrue(obj);
        XXH32_update(hash_state, &TYPE_BOOL, sizeof(TYPE_BOOL));
        XXH32_update(hash_state, &value, sizeof(value));
    } else if (PyUnicode_Check(obj)) {
        /* Python - str */
        Py_ssize_t length;
        const char* data = PyUnicode_AsUTF8AndSize(obj, &length);
        XXH32_update(hash_state, &TYPE_STR, sizeof(TYPE_STR));
        XXH32_update(hash_state, data, (size_t)length);
    }  else {
        // Set TypeError for unknown primitive type
        PyErr_SetString(PyExc_TypeError, "Unsupported object type for hashing");
        XXH32_freeState(hash_state);
        return NULL;
    }

    VisitorReturnType result;
    result.hashed_state = hash_state;

    return result;
}

VisitorReturnType hash_visit_tuple(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}
VisitorReturnType hash_visit_list(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}
VisitorReturnType hash_visit_set(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}
VisitorReturnType hash_visit_dict(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}
VisitorReturnType hash_visit_byte(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}
VisitorReturnType hash_visit_type(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}
VisitorReturnType hash_visit_callable(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}
VisitorReturnType hash_visit_custom_obj(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}
VisitorReturnType hash_visit_other(PyObject *obj, long *visited, int include_id, XXH32_state_t *hash_state) {}


HashVisitor* create_hash_visitor() {
    int seed = 0;
    HashVisitor* visitor = (HashVisitor*)malloc(sizeof(HashVisitor));
    visitor->base.check_visited = hash_check_visited;
    visitor->base.visit_primitive = hash_visit_primitive;
    visitor->base.visit_tuple = hash_visit_tuple;
    visitor->base.visit_list = hash_visit_list;
    visitor->base.visit_set = hash_visit_set;
    visitor->base.visit_dict = hash_visit_dict;
    visitor->base.visit_byte = hash_visit_byte;
    visitor->base.visit_type = hash_visit_type;
    visitor->base.visit_callable = hash_visit_callable;
    visitor->base.visit_custom_obj = hash_visit_custom_obj;
    visitor->base.visit_other = hash_visit_other;

    XXH32_state_t* state = XXH32_createState();
    XXH32_reset(state, seed);
    return visitor;
}