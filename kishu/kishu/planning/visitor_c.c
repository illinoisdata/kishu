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

VisitorReturnType get_object_hash(PyObject *obj) {
    HashVisitor* hash_visitor = create_hash_visitor();
}

// VisitorReturnType get_object_state(PyObject *obj, Visitor visitor, int include_id, XXH32_state_t* hash_state) {}