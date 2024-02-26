#ifndef _HASH_VISITOR_C_H
#define _HASH_VISITOR_C_H

#include "visitor_c.h"

// typedef struct HashVisitor {
//     Visitor base; // First member is Visitor
//     // Additional members specific to HashVisitor
// } HashVisitor;

Visitor* create_hash_visitor();

VisitorReturnType* hash_has_visited(PyObject *obj, Visited *visited, const bool include_id, VisitorReturnType* state);
VisitorReturnType* hash_handle_visited(PyObject *obj, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_primitive(PyObject *obj, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_tuple(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_list(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_set(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_dict(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_byte(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_type(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_callable(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
VisitorReturnType* hash_visit_custom_obj(PyObject *obj, Visited **visited, const bool include_id, VisitorReturnType* state, PyObject* list_included, const bool include_trav);
void hash_free_contents(Visited *visited, VisitorReturnType* state);
// PyObject* get_obj_id(PyObject *v);

#endif /* _HASH_VISITOR_C_H */