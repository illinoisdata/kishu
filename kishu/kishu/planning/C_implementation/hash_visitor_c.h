#ifndef _HASH_VISITOR_C_H
#define _HASH_VISITOR_C_H

#include "visitor_c.h"

// typedef struct HashVisitor {
//     Visitor base; // First member is Visitor
//     // Additional members specific to HashVisitor
// } HashVisitor;

Visitor* create_hash_visitor();

VisitorReturnType* hash_has_visited(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_handle_visited(PyObject *obj, Visited *visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_primitive(PyObject *obj, VisitorReturnType* state);
VisitorReturnType* hash_visit_tuple(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_list(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_set(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_dict(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_byte(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_type(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_callable(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_custom_obj(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);
VisitorReturnType* hash_visit_other(PyObject *obj, Visited **visited, int include_id, VisitorReturnType* state);


#endif /* _HASH_VISITOR_C_H */