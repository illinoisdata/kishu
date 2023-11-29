#ifndef _HASH_VISITOR_C_H
#define _HASH_VISITOR_C_H

#include "visitor_c.h"

typedef struct HashVisitor {
    Visitor base; // First member is Visitor
    // Additional members specific to HashVisitor
} HashVisitor;

HashVisitor* create_hash_visitor();

long* hash_check_visited(long *visited, long id, PyObject *include_id);
VisitorReturnType hash_visit_primitive(PyObject *obj, PyObject *hash_state);
VisitorReturnType hash_visit_tuple(PyObject *obj, long *visited, int include_id, PyObject *hash_state);
VisitorReturnType hash_visit_list(PyObject *obj, long *visited, int include_id, PyObject *hash_state);
VisitorReturnType hash_visit_set(PyObject *obj, long *visited, int include_id, PyObject *hash_state);
VisitorReturnType hash_visit_dict(PyObject *obj, long *visited, int include_id, PyObject *hash_state);
VisitorReturnType hash_visit_byte(PyObject *obj, long *visited, int include_id, PyObject *hash_state);
VisitorReturnType hash_visit_type(PyObject *obj, long *visited, int include_id, PyObject *hash_state);
VisitorReturnType hash_visit_callable(PyObject *obj, long *visited, int include_id, PyObject *hash_state);
VisitorReturnType hash_visit_custom_obj(PyObject *obj, long *visited, int include_id, PyObject *hash_state);
VisitorReturnType hash_visit_other(PyObject *obj, long *visited, int include_id, PyObject *hash_state);


#endif /* _HASH_VISITOR_C_H */