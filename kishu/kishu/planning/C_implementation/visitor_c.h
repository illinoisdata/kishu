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

typedef struct Visited {
    PyObject *pyObject;
    struct Visited *next;
} Visited

// function pointer for visitor pattern

typedef struct Visitor {
    Visited* (*has_visited)(Visited *visited, PyObject *obj, int include_id);
    VisitorReturnType* (*visit_primitive)(PyObject *obj, VisitorReturnType* state);
    VisitorReturnType* (*visit_tuple)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    VisitorReturnType* (*visit_list)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    VisitorReturnType* (*visit_set)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    VisitorReturnType* (*visit_dict)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    VisitorReturnType* (*visit_byte)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    VisitorReturnType* (*visit_type)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    VisitorReturnType* (*visit_callable)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    VisitorReturnType* (*visit_custom_obj)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    VisitorReturnType* (*visit_other)(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
    Visited* visited;
    VisitorReturnType* state;
} Visitor;

static PyObject* get_object_hash_wrapper(PyObject* self, PyObject* args);

VisitorReturnType* get_object_state(PyObject *obj, Visitor *visitor, int include_id, VisitorReturnType* state);
VisitorReturnType* get_object_hash(PyObject *obj);

int is_primitive(PyObject *obj);

PyMODINIT_FUNC PyInit_VisitorModule(void);

#endif /* _VISITOR_C_H */