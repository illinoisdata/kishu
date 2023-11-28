#ifndef _HASH_VISITOR_C_H
#define _HASH_VISITOR_C_H

#include "visitor_c.h"

// Global type identifiers
extern const int TYPE_NONE;
extern const int TYPE_NOTIMPLEMENTED;
extern const int TYPE_ELLIPSIS;
extern const int TYPE_INT;
extern const int TYPE_FLOAT;
extern const int TYPE_BOOL;
extern const int TYPE_STR;

long* hash_check_visited(long *visited, long id, PyObject *include_id);
VisitorReturnType hash_visit_primitive(PyObject *obj, PyObject *hash_state);
VisitorReturnType hash_visit_tuple(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);
VisitorReturnType hash_visit_list(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);
VisitorReturnType hash_visit_set(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);
VisitorReturnType hash_visit_dict(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);
VisitorReturnType hash_visit_byte(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);
VisitorReturnType hash_visit_type(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);
VisitorReturnType hash_visit_callable(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);
VisitorReturnType hash_visit_custom_obj(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);
VisitorReturnType hash_visit_other(PyObject *obj, long *visited, PyObject *include_id, PyObject *hash_state);


#endif /* _HASH_VISITOR_C_H */