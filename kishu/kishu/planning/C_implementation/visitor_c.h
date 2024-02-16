#ifndef _VISITOR_C_H
#define _VISITOR_C_H

#include <Python.h>
#include <stdbool.h>
#include "xxhash.h"

// Global type identifiers
extern const int TYPE_NONE;
extern const int TYPE_NOTIMPLEMENTED;
extern const int TYPE_ELLIPSIS;
extern const int TYPE_INT;
extern const int TYPE_FLOAT;
extern const int TYPE_BOOL;
extern const int TYPE_STR;
extern const int TYPE_BYTE;
extern const int TYPE_BYTEARR;


typedef union {
    PyObject* py_object;
    XXH3_state_t* hashed_state;
    // GraphNode* node;
    // other possible return types
} VisitorReturnType;

typedef struct Visited {
    PyObject *pyObject;
    // PyObject *id;
    struct Visited *next;
    // maybe have a pointer here to the VisitorReturnType as well
} Visited;

// function pointer for visitor pattern

typedef struct Visitor {
    VisitorReturnType* (*has_visited)(PyObject *obj, Visited *visited, const bool include_id, VisitorReturnType* state);
    VisitorReturnType* (*handle_visited)(PyObject *obj, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_primitive)(PyObject *obj, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_tuple)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_list)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_set)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_dict)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_byte)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_type)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_callable)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_custom_obj)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included);
    VisitorReturnType* (*visit_other)(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state);
    void (*update_state_id)(PyObject *obj, VisitorReturnType* state, PyObject* list_included);
    Visited* visited;
    PyObject* list_included; // for debugging purposes
    VisitorReturnType* state;
} Visitor;

// static PyObject* get_object_hash_wrapper(PyObject* self, PyObject* args);

VisitorReturnType* get_object_state(PyObject *obj, Visitor *visitor, const bool include_id, VisitorReturnType* state);
// VisitorReturnType* get_object_hash(PyObject *obj);
Visitor* get_object_hash(PyObject *obj);

Visitor* get_hash_visitor();

int is_primitive(PyObject *obj);
int is_picklable(PyObject *obj);
int is_pandas_RangeIndex_instance(PyObject *obj);
int is_plt_Callback_instance(PyObject *obj);
int is_pickable_using_Python(PyObject *obj);

PyMODINIT_FUNC PyInit_VisitorModule(void);

#endif /* _VISITOR_C_H */