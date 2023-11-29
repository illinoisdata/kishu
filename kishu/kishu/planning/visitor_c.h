#ifndef _VISITOR_C_H
#define _VISITOR_C_H

#include <Python.h>

// Global type identifiers
extern const int TYPE_NONE;
extern const int TYPE_NOTIMPLEMENTED;
extern const int TYPE_ELLIPSIS;
extern const int TYPE_INT;
extern const int TYPE_FLOAT;
extern const int TYPE_BOOL;
extern const int TYPE_STR;


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
    VisitorReturnType (*visit_tuple)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_list)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_set)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_dict)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_byte)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_type)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_callable)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_custom_obj)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    VisitorReturnType (*visit_other)(PyObject *obj, long *visited, int include_id, XXH32_state_t* hash_state);
    long* visited;
} Visitor;

VisitorReturnType get_object_hash(PyObject *obj);

#endif /* _VISITOR_C_H */