#ifndef _VISITOR_C_H
#define _VISITOR_C_H

#include <Python.h>


// Definitions of global type identifiers
const int TYPE_NONE = 0;
const int TYPE_NOTIMPLEMENTED = 1;
const int TYPE_ELLIPSIS = 2;
const int TYPE_INT = 3;
const int TYPE_FLOAT = 4;
const int TYPE_BOOL = 5;
const int TYPE_STR = 6;


typedef union {
    PyObject* py_object;
    XXH32_state_t* hashed_state;
    // GraphNode* node;
    // other possible return types
} VisitorReturnType;

// function pointer for visitor pattern
typedef struct Visitor {
    long* (*check_visited)(long *visited, long id, PyObject *include_id);
    VisitorReturnType (*visit_primitive)(PyObject *obj, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_tuple)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_list)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_set)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_dict)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_byte)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_type)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_callable)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_custom_obj)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_other)(PyObject *obj, long *visited, PyObject *include_id, XXH32_state_t* hash_state);
    long* visited;
} Visitor;

#endif /* _VISITOR_C_H */