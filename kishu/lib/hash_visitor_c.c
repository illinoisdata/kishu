#include <Python.h>
#include <stdbool.h>
#include "hash_visitor_c.h"
#include "xxhash.h"


/*
* Checks if the hash visitor has already visited this object.
* If it has, the function return the state, otherwise it returns NULL
*/
VisitorReturnType* hash_has_visited(PyObject *obj, Visited *visited, const bool include_id, VisitorReturnType* state) {
    // Implementation specific to HashVisitor

    Visited* current = visited;
    while(current != NULL) {
        if (current->pyObject == obj)
            return state;
        current = current->next;
    }
    return NULL;
}

VisitorReturnType* hash_handle_visited(PyObject *obj,const bool include_id, VisitorReturnType* state, PyObject* list_included) {
    if (include_id) {
        /* Hash id */

        size_t obj_id = (size_t)obj;
        XXH3_64bits_update(state->hashed_state, &obj_id, sizeof(obj_id));

        PyList_Append(list_included, PyLong_FromLongLong(obj_id));
    }
    return state;
}

// Handles int, float, bool, str, None, NotImplemented, Ellipsis, bytes, bytearray
VisitorReturnType* hash_visit_primitive(PyObject *obj, VisitorReturnType* state, PyObject* list_included) {
    if (obj == Py_None) {
        /* Python - None */
        XXH3_64bits_update(state->hashed_state, &TYPE_NONE, sizeof(TYPE_NONE));
        PyList_Append(list_included, obj);
    } else if (obj == Py_NotImplemented) {
        /* Python - NotImplemented */
        XXH3_64bits_update(state->hashed_state, &TYPE_NOTIMPLEMENTED, sizeof(TYPE_NOTIMPLEMENTED));
        PyList_Append(list_included, obj);
    } else if (obj == Py_Ellipsis) {
        /* Python - Ellipsis */
        XXH3_64bits_update(state->hashed_state, &TYPE_ELLIPSIS, sizeof(TYPE_ELLIPSIS));
        PyList_Append(list_included, obj);
    } else if (PyLong_Check(obj)) {
        /* Python - int */
        size_t value = PyLong_AsLongLong(obj);
        XXH3_64bits_update(state->hashed_state, &TYPE_INT, sizeof(TYPE_INT));
        XXH3_64bits_update(state->hashed_state, &value, sizeof(value));

        PyList_Append(list_included, obj);
    } else if (PyFloat_Check(obj)) {
        /* Python - float */
        double value = PyFloat_AsDouble(obj);
        XXH3_64bits_update(state->hashed_state, &TYPE_FLOAT, sizeof(TYPE_FLOAT));
        XXH3_64bits_update(state->hashed_state, &value, sizeof(value));

        PyList_Append(list_included, obj);
    } else if (PyBool_Check(obj)) {
        /* Python - bool */
        long value = PyObject_IsTrue(obj);
        XXH3_64bits_update(state->hashed_state, &TYPE_BOOL, sizeof(TYPE_BOOL));
        XXH3_64bits_update(state->hashed_state, &value, sizeof(value));

        PyList_Append(list_included, obj);
    } else if (PyUnicode_Check(obj)) {
        /* Python - str */
        Py_ssize_t length;
        const char* data = PyUnicode_AsUTF8AndSize(obj, &length);
        XXH3_64bits_update(state->hashed_state, &TYPE_STR, sizeof(TYPE_STR));
        XXH3_64bits_update(state->hashed_state, data, (size_t)length);

        PyList_Append(list_included, obj);
    }  else {
        // Set TypeError for unknown primitive type
        PyErr_SetString(PyExc_TypeError, "Unsupported object type for hashing");
        XXH3_freeState(state->hashed_state);
        return NULL;
    }

    return state;
}

VisitorReturnType* hash_visit_tuple(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included) {
    return state;
}

VisitorReturnType* hash_visit_list(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included) {
    Visited *new_node = (Visited*) (malloc(sizeof(Visited)));
    new_node->next = *visited;
    new_node->pyObject = obj;
    *visited = new_node;

    if (include_id) {
        /* Hash id */
        size_t obj_id = (size_t)obj;
        XXH3_64bits_update(state->hashed_state, &obj_id, sizeof(obj_id));

        PyList_Append(list_included, PyLong_FromLongLong(obj_id));
    }
    return state;
}

VisitorReturnType* hash_visit_set(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included) {
    Visited *new_node = (Visited*) (malloc(sizeof(Visited)));
    new_node->next = *visited;
    new_node->pyObject = obj;
    *visited = new_node;

    if (include_id) {
        size_t obj_id = (size_t)obj;
        XXH3_64bits_update(state->hashed_state, &obj_id, sizeof(obj_id));

        PyList_Append(list_included, PyLong_FromLongLong(obj_id));
    }  
    return state;
}

VisitorReturnType* hash_visit_dict(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included) {
    Visited *new_node = (Visited*) (malloc(sizeof(Visited)));
    new_node->next = *visited;
    new_node->pyObject = obj;
    *visited = new_node;

    if (include_id) {
        size_t obj_id = (size_t)obj;
        XXH3_64bits_update(state->hashed_state, &obj_id, sizeof(obj_id));

        PyList_Append(list_included, PyLong_FromLongLong(obj_id));
    }  
    return state;
}

VisitorReturnType* hash_visit_byte(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included) {
    /* Python - bytes or bytearray */
    char *data;
    Py_ssize_t length;

    if (PyBytes_Check(obj)) {
        data = PyBytes_AsString(obj);
        length = PyBytes_Size(obj);
    } else { // PyByteArray_Check(obj)
        data = PyByteArray_AsString(obj);
        length = PyByteArray_Size(obj);
    }

    if (!data) {
        // error: data is NULL
        return NULL;
    }
    /* Hash type */
    if (PyBytes_Check(obj)) {
        XXH3_64bits_update(state->hashed_state, &TYPE_BYTE, sizeof(TYPE_BYTE));
    }
    else {
        XXH3_64bits_update(state->hashed_state, &TYPE_BYTEARR, sizeof(TYPE_BYTEARR));
    }

    /* Hash value */
    XXH3_64bits_update(state->hashed_state, data, (size_t)length);

    PyList_Append(list_included, obj);
    return state;
}

VisitorReturnType* hash_visit_type(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included) {
    /* Python - type */
    const char* typeName = ((PyTypeObject*)obj)->tp_name;
    if (!typeName) {
        // Handle error: typeName is NULL
        return NULL;
    }
    XXH3_64bits_update(state->hashed_state, typeName, strlen(typeName));

    PyList_Append(list_included, obj);
    return state;
}

VisitorReturnType* hash_visit_callable(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included) {


    if (include_id) {
        Visited *new_node = (Visited*) (malloc(sizeof(Visited)));
        new_node->next = *visited;
        new_node->pyObject = obj;
        *visited = new_node;
        
        size_t obj_id = (size_t)obj;
        XXH3_64bits_update(state->hashed_state, &obj_id, sizeof(obj_id));

        PyList_Append(list_included, PyLong_FromLongLong(obj_id));
    }

    return state;
}

VisitorReturnType* hash_visit_custom_obj(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included) {
    Visited *new_node = (Visited*) (malloc(sizeof(Visited)));
    new_node->next = *visited;
    new_node->pyObject = obj;
    *visited = new_node;

    return state;
}

VisitorReturnType* hash_visit_other(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state) {return NULL;}

void hash_update_state_id(PyObject *obj, VisitorReturnType* state, PyObject* list_included) {
    size_t obj_id = (size_t)obj;
    XXH3_64bits_update(state->hashed_state, &obj_id, sizeof(obj_id)); 

    PyList_Append(list_included, PyLong_FromLongLong(obj_id));
}


Visitor* create_hash_visitor() {
    int seed = 0;
    /* Initialze hash visitor */
    Visitor* visitor = (Visitor*) (malloc(sizeof(Visitor)));
    /* Initialize hash visitor functions */
    visitor->has_visited = hash_has_visited;
    visitor->handle_visited = hash_handle_visited;

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

    visitor->update_state_id = hash_update_state_id;

    visitor->visited = NULL;

    XXH3_state_t* xxhash_state = XXH3_createState();
    XXH3_64bits_reset_withSeed(xxhash_state, seed);

    VisitorReturnType* state = (VisitorReturnType*) (malloc(sizeof(VisitorReturnType*)));
    state->hashed_state = xxhash_state;

    /* Initialize hash visitor state */
    visitor->state = state;

    visitor->list_included = PyList_New(0);
    
    return visitor;
}
