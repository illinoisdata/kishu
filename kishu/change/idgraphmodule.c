#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "cJSON.h"
#include <string.h>
#include "xxhash.h"
#include <stdbool.h>
// # include "ndarraytypes.h"
#include "numpy/arrayobject.h"

// Forward declaration
typedef struct idGraphNode idGraphNode;
idGraphNode *create_id_graph();

/**
 * A union to represent obj_value idGraphPrimitiveValue.
 *
 * @member "next" Pointer to the next node.
 * @member "child" Pointer to the idGraphNode represented by the node.
 **/
typedef union
{
    long long obj_int;   // Value for integer types
    double obj_float;    // Value for float types
    bool obj_bool;       // Value for bool types
    const char *obj_str; // Value for string types
} idGraphPrimitiveValue;

/**
 * A struct to represent a linkedlist node holding an idGraphNode.
 *
 * @member "next" Pointer to the next node.
 * @member "child" Pointer to the idGraphNode represented by the node.
 **/
typedef struct idGraphNodeList
{
    struct idGraphNodeList *next;
    idGraphNode *child;
} idGraphNodeList;

/**
 * A struct to represent an ID Graph node.
 * @member "obj_id" Unique object id (memory address).
 * @member "obj_type" Type of object.
 * @member "is_primitive" If node represents a primitive type.
 * @member "primitive" Union that holds primitive value.
 * @member "children" Head of a linklist representing children of the object.
 **/
enum IdGraphObjectType
{
    OBJ_TYPE_INT,
    OBJ_TYPE_FLOAT,
    OBJ_TYPE_BOOL,
    OBJ_TYPE_STRING,
    OBJ_TYPE_LIST,
    OBJ_TYPE_TUPLE,
    OBJ_TYPE_DICT,
    OBJ_TYPE_SET,
    OBJ_TYPE_CLASS,
};

char *getobjectTypeName(enum IdGraphObjectType graphObjectType)
{
    switch (graphObjectType)
    {
    case OBJ_TYPE_INT:
        return "int";
    case OBJ_TYPE_FLOAT:
        return "float";
    case OBJ_TYPE_BOOL:
        return "bool";
    case OBJ_TYPE_STRING:
        return "string";
    case OBJ_TYPE_LIST:
        return "list";
    case OBJ_TYPE_TUPLE:
        return "tuple";
    case OBJ_TYPE_DICT:
        return "dict";
    case OBJ_TYPE_SET:
        return "set";
    case OBJ_TYPE_CLASS:
        return "class";
    default:
        return "unknown";
    }
}

struct idGraphNode
{
    long obj_id;                    // Pointer to memory address
    enum IdGraphObjectType obj_type; // Type of object
    bool is_primitive;
    idGraphPrimitiveValue primitive; // Union to the primitive value
    idGraphNodeList *children;
};


/**
 * Constructs a cJSON object representation of the ID Graph (idGraphNode *).
 *
 * Recursively iterates over the ID graph and creates a JSON object.
 *
 * @param node Head node of the ID graph.
 *
 * @return Returns the computed cJSON object.
 **/
cJSON *get_json_rep(idGraphNode *node)
{

    cJSON *node_json = cJSON_CreateObject();

    // Add the object id and type as JSON string values
    // Allocate memory for the string representation of obj_id
    if (node->is_primitive == false)
    {
        // char obj_id[64];
        // snprintf(obj_id, sizeof(obj_id), "%ld", node->obj_id);
        cJSON_AddNumberToObject(node_json, "obj_id", node->obj_id);
    }
    else
    {
        char *obj_val;
        if (node->obj_type == OBJ_TYPE_INT)
        {
            size_t id_size = snprintf(NULL, 0, "%lld", node->primitive.obj_int);
            int len = id_size + 1;
            obj_val = malloc(len * sizeof(char)); // Memory freed later
            snprintf(obj_val, len, "%lld", node->primitive.obj_int);
        }
        else if (node->obj_type == OBJ_TYPE_FLOAT)
        {
            size_t id_size = snprintf(NULL, 0, "%lf", node->primitive.obj_float);
            int len = id_size + 1;
            obj_val = malloc(len * sizeof(char)); // Memory freed later
            snprintf(obj_val, len, "%lf", node->primitive.obj_float);
        }
        else if (node->obj_type == OBJ_TYPE_BOOL)
        {
            size_t id_size = snprintf(NULL, 0, "%d", node->primitive.obj_bool);
            int len = id_size + 1;
            obj_val = malloc(len * sizeof(char)); // Memory freed later
            snprintf(obj_val, len, "%d", node->primitive.obj_bool);
        }
        else if (node->obj_type == OBJ_TYPE_STRING)
        {
            size_t id_size = snprintf(NULL, 0, "%s", node->primitive.obj_str);
            int len = id_size + 1;
            obj_val = malloc(len * sizeof(char)); // Memory freed later
            snprintf(obj_val, len, "%s", node->primitive.obj_str);
        }
        else
        {
            obj_val = "unknown";
        }
        cJSON_AddStringToObject(node_json, "obj_val", obj_val);
        free(obj_val);
        obj_val = NULL;
    }

    cJSON_AddStringToObject(node_json, "obj_type", getobjectTypeName(node->obj_type));

    cJSON *children_array = cJSON_CreateArray();
    cJSON_AddItemToObject(node_json, "children", children_array);
    idGraphNodeList *child_node = node->children;
    while (child_node != NULL)
    {
        cJSON_AddItemToArray(children_array, get_json_rep(child_node->child));
        child_node = child_node->next;
    }
    return node_json;
}

/**
 * Generates a JSON string of the ID Graph (idGraphNode *).
 *
 * Calls get_json_rep and converts the JSON object into string.
 *
 * @param node Head node of the ID graph.
 *
 * @return Returns the computed JSON string.
 **/
char *get_json_str(idGraphNode *node)
{
    cJSON *jsonRep = get_json_rep(node);
    char *jsonString = cJSON_Print(jsonRep);
    cJSON_Delete(jsonRep);
    return jsonString;
}

/**
 * Adds a child idGraphNode to a parent idGraphNode.
 *
 * @param parent Parent node.
 * @param child Child node.
 **/
void add_child(idGraphNode *parent, idGraphNode *child)
{
    idGraphNodeList *new_node = (idGraphNodeList *)malloc(sizeof(idGraphNodeList));
    new_node->child = child;
    new_node->next = parent->children;
    parent->children = new_node;
}

/**
 * Searches for an ID graph node in a linkedlist.
 *
 * @param list The idGraphNodeList to search in.
 * @param id The id of the idGraphNode being serched.
 *
 * @return Returns the the ID graph node(idGraphNode *) if exists
 * else returns NULL
 **/
idGraphNode *find_idGraphNode_in_list(idGraphNodeList *list, long id)
{
    idGraphNodeList *current = list;
    while (current != NULL)
    {
        if (current->child->obj_id == id)
        {
            return current->child;
        }
        current = current->next;
    }
    return NULL;
}

/**
 * Adds an ID graph node to the visited list.
 *
 * @param visited The idGraphNodeList.
 * @param node The node to be added to viited list.
 **/
idGraphNodeList *mark_visited(idGraphNodeList *visited, idGraphNode *node)
{
    idGraphNodeList *new_node = malloc(sizeof(idGraphNodeList));
    new_node->next = visited;
    new_node->child = node;
    return new_node;
}

/**
 * Initializes an idGraphNode
 *
 * @param obj_id The object id to be used as initial value.
 * @param obj_type The object type to be used as initial value.
 **/
idGraphNode *create_idGraphNode(long obj_id, enum IdGraphObjectType obj_type, bool primitive)
{
    idGraphNode *node = (idGraphNode *)malloc(sizeof(idGraphNode));
    node->obj_id = obj_id;
    node->obj_type = obj_type;
    node->children = NULL;
    node->is_primitive = primitive;
    return node;
}

const long get_builtin_id(PyObject *v) {
    if (v == NULL) {
        return 0;
    }

    PyObject *id = PyLong_FromVoidPtr(v);

    if (id && PySys_Audit("builtins.id", "O", id) < 0) {
        Py_DECREF(id);
        return 0;
    }

    return PyLong_AsLong(id);
}

/**
 * Iterates over a list of tuple and adds children nodes to the ID graph.
 **/
void process_collection_items(PyObject *obj, idGraphNode *node, idGraphNodeList *visited)
{
    Py_ssize_t size = PySequence_Size(obj);
    for (Py_ssize_t i = 0; i < size; i++)
    {
        PyObject *item = PySequence_GetItem(obj, i);
        long id = get_builtin_id(item);
        idGraphNode *child = find_idGraphNode_in_list(visited, id);
        if (child == NULL)
        {
            child = create_id_graph(item, visited);
        }
        else
        {
            child = create_idGraphNode(child->obj_id, child->obj_type, 0);
        }
        if (child != NULL)
        {
            add_child(node, child);
        }
    }
}

/**
 * Computes an ID graph(idGraphNode *) for any python object.
 *
 * Recursively iterates over the children of the given python object
 * and stores the objectId(memory address) and type of objects
 * that fall under one of these categories (list, set, tuple, dictionary, class instance).
 *
 * We maintain a visited objects list to identify cyclic references.
 * For cyclically referenced objects, we only store the id of the visited object to avoid infinite loop.
 *
 * @param obj A python object.
 * @param visited A list of visited objects.
 *
 * @return Returns the head of the ID graph (idGraphNode *)
 **/
idGraphNode *create_id_graph(PyObject *obj, idGraphNodeList *visited)
{
    idGraphNode *node = NULL;
    const long builtin_id = get_builtin_id(obj);
    // List
    if (PyList_Check(obj))
    {
        node = create_idGraphNode(builtin_id, OBJ_TYPE_LIST, 0);
        visited = mark_visited(visited, node);
        process_collection_items(obj, node, visited);
    }
    // Tuple
    else if (PyTuple_Check(obj))
    {
        node = create_idGraphNode(builtin_id, OBJ_TYPE_TUPLE, 0);
        visited = mark_visited(visited, node);
        process_collection_items(obj, node, visited);
    }
    // Dictionary
    else if (PyDict_Check(obj))
    {
        node = create_idGraphNode(builtin_id, OBJ_TYPE_DICT, 0);
        visited = mark_visited(visited, node);
        PyObject *keys = PyDict_Keys(obj);
        PyObject *values = PyDict_Values(obj);
        Py_ssize_t size = PyList_Size(keys);
        for (Py_ssize_t i = 0; i < size; i++)
        {
            PyObject *key = PyList_GetItem(keys, i);
            PyObject *value = PyList_GetItem(values, i);

            // add key
            long id = get_builtin_id(key);
            idGraphNode *child = find_idGraphNode_in_list(visited, id);
            if (child == NULL)
            {
                child = create_id_graph(key, visited);
            }
            else
            {
                idGraphNode *visited_child = (idGraphNode *)malloc(sizeof(idGraphNode)); // Memory freed later
                visited_child->obj_id = child->obj_id;
                visited_child->obj_type = child->obj_type;
                visited_child->children = NULL;
                child = visited_child;
                free(visited_child);
                visited_child = NULL;
            }
            if (child != NULL)
            {
                add_child(node, child);
            }

            // add value
            id = get_builtin_id(value);
            child = find_idGraphNode_in_list(visited, id);
            if (child == NULL)
            {
                child = create_id_graph(value, visited);
            }
            else
            {
                // TODO: free this memory
                idGraphNode *visited_child = (idGraphNode *)malloc(sizeof(idGraphNode));
                visited_child->obj_id = child->obj_id;
                visited_child->obj_type = child->obj_type;
                visited_child->children = NULL;
                child = visited_child;
                visited_child = NULL;
            }
            if (child != NULL)
            {
                add_child(node, child);
            }
        }
    }
    // Set
    else if (PyAnySet_Check(obj))
    {
        node = create_idGraphNode(builtin_id, OBJ_TYPE_SET, 0);
        visited = mark_visited(visited, node);

        PyObject *iter = PyObject_GetIter(obj);
        PyObject *item;
        while ((item = PyIter_Next(iter)))
        {
            long id = get_builtin_id(item);
            idGraphNode *child = find_idGraphNode_in_list(visited, id);
            if (child == NULL)
            {
                child = create_id_graph(item, visited);
            }
            else
            {
                // TODO: free this memory
                idGraphNode *visited_child = (idGraphNode *)malloc(sizeof(idGraphNode));
                visited_child->obj_id = child->obj_id;
                visited_child->obj_type = child->obj_type;
                visited_child->children = NULL;
                child = visited_child;
                visited_child = NULL;
            }
            if (child != NULL)
            {
                add_child(node, child);
            }
        }
    }
    
    // Bool
    else if (PyBool_Check(obj))
    {
        int val = PyObject_IsTrue(obj);
        node = create_idGraphNode(builtin_id, OBJ_TYPE_BOOL, true);
        node->primitive.obj_int = val;
    }
    // Long(Integers)
    else if (PyLong_Check(obj))
    {
        long val = PyLong_AsLong(obj);
        node = create_idGraphNode(builtin_id, OBJ_TYPE_INT, true);
        node->primitive.obj_int = val;
    }
    // Float(Floating point)
    else if (PyFloat_Check(obj))
    {
        double val = PyFloat_AsDouble(obj);
        node = create_idGraphNode(builtin_id, OBJ_TYPE_FLOAT, true);
        node->primitive.obj_float = val;
    }
    // String
    else if (PyUnicode_Check(obj))
    {
        // PySys_WriteStdout("string made \n");
        const char *val = PyUnicode_AsUTF8(obj);
        // PySys_WriteStdout("%d \n", *val);
        node = create_idGraphNode(builtin_id, OBJ_TYPE_STRING, true);
        node->primitive.obj_str = val;

    }

    // Numpy Arrays
    else if (strcmp(PyUnicode_AsUTF8(PyObject_GetAttrString(PyObject_Type(obj), "__name__")), "ndarray") == 0)
    {
        import_array();

        PyArrayObject* arr_obj = (PyArrayObject*)obj; 
        const long builtin_id_2 = (long)(PyArray_BASE(arr_obj));
        
        if (builtin_id_2 == 0)
            node = create_idGraphNode(builtin_id, OBJ_TYPE_CLASS, 0);
        else
            node = create_idGraphNode(builtin_id_2, OBJ_TYPE_CLASS, 0);

        visited = mark_visited(visited, node);

        npy_intp arr_len = PyArray_SIZE(arr_obj);
        for (npy_intp i = 0; i < arr_len; ++i) {
            PyObject *item = PyArray_GETITEM(arr_obj, PyArray_DATA(arr_obj) + i * PyArray_ITEMSIZE(arr_obj));

            long id = get_builtin_id(item);
            idGraphNode *child = find_idGraphNode_in_list(visited, id);
            if (child == NULL)
            {
                child = create_id_graph(item, visited);
            }
            else
            {
                child = create_idGraphNode(child->obj_id, child->obj_type, 0);
            }
            if (child != NULL)
            {
                add_child(node, child);
            }
        }

    }

    // Other Class object
    else if (!PyModule_Check(obj) && !PyType_Check(obj) && obj != NULL)
    {
        node = create_idGraphNode(builtin_id, OBJ_TYPE_CLASS, 0);
        visited = mark_visited(visited, node);

        PyObject *dir = PyObject_Dir(obj);

        if (dir != NULL && PyList_Check(dir)) {

            Py_ssize_t dir_len = PyList_Size(dir);

            // Attributes to exclude from idgraph
            char exclude_dir1[] = "T"; // This attribute, found in dataframe and series objects, are of the types dataframe and series, and thus iterating through them would result in an infinite loop
            char exclude_dir2[] = "__doc__"; // This attribute contains the documentation of the object
            char exclude_dir3[] = "imag"; // This attribute, found in numpy arrays, contain numpy arrays and thus iterating through them would result in an infinite loop
            char exclude_dir4[] = "real"; // This attribute, found in numpy arrays, contain numpy arrays and thus iterating through them would result in an infinite loop

            for (Py_ssize_t i = 0; i < dir_len; i++) {
                PyObject *attr_title = PyList_GetItem(dir, i);
                const char *name = PyUnicode_AsUTF8(attr_title);

                if (name != NULL) {
                    if((strcmp(name, exclude_dir1) == 0) || (strcmp(name, exclude_dir2) == 0))
                        continue;
                }

                if (name[0] == '_') {
                    continue;
                }

                PyObject *attr = PyObject_GetAttr(obj, attr_title);
                PyObject *type_name = PyObject_GetAttrString(PyObject_Type(attr), "__name__");

                const char *name2 = PyUnicode_AsUTF8(type_name);

                if (PyList_Check(attr) || PyTuple_Check(attr) || PyDict_Check(attr) || PyAnySet_Check(attr) || PyBool_Check(attr) || PyLong_Check(attr) || PyFloat_Check(attr) || PyUnicode_Check(attr) || (strcmp(name2,"ndarray") == 0) || (strcmp(name2,"Series") == 0)) {
                    
                    // Creating idgraphs of attributes imag or real of type numpy array can result in an infinite loop since each numpy array consists of imag and real numpy array attributes
                    if ((strcmp(name, exclude_dir3) == 0) && (strcmp(name2,"ndarray") == 0))
                        continue;
                    if ((strcmp(name, exclude_dir4) == 0) && (strcmp(name2,"ndarray") == 0))
                        continue;
                
                    if (name != NULL) {
                        // check if id remains constant if object is unchanged (excluding numpy array and primitive objects)
                        if (strcmp(name2,"ndarray") != 0 && !PyBool_Check(attr) && !PyLong_Check(attr) && !PyFloat_Check(attr) && !PyUnicode_Check(attr)) {          
                            if (get_builtin_id(PyObject_GetAttr(obj, attr_title)) != get_builtin_id(PyObject_GetAttr(obj, attr_title))) {
                                continue;
                            }
                        }

                        // insert attribute name
                        long id = get_builtin_id(attr_title);
                        idGraphNode *child = find_idGraphNode_in_list(visited, id);
                        if (child == NULL) {
                            child = create_id_graph(attr_title, visited);
                        }
                        else {
                            idGraphNode *visited_child = (idGraphNode *)malloc(sizeof(idGraphNode));
                            visited_child->obj_id = child->obj_id;
                            visited_child->obj_type = child->obj_type;
                            visited_child->children = NULL;
                            child = visited_child;
                            visited_child = NULL;
                        }
                        if (child != NULL) {
                            add_child(node, child);
                        }

                        // insert attribute contents
                        id = get_builtin_id(attr);
                        idGraphNode *child2 = find_idGraphNode_in_list(visited, id);
                        if (child2 == NULL) {
                            child2 = create_id_graph(attr, visited);
                        }
                        else {
                            idGraphNode *visited_child = (idGraphNode *)malloc(sizeof(idGraphNode));
                            visited_child->obj_id = child2->obj_id;
                            visited_child->obj_type = child2->obj_type;
                            visited_child->children = NULL;
                            child2 = visited_child;
                            visited_child = NULL;
                        }
                        if (child2 != NULL) {
                            add_child(child, child2);
                        }
                    }
                }
            }
        } 
    }

    // Not implemented  objects
    else
    {
        PyErr_SetString(PyExc_NotImplementedError, "Unsupported type.");
        return NULL;
    }

    return node;
}

/**
 * Returns the ID graph(idGraphNode *) as PyCapsule object.
 *
 * This method is exposed to the Python caller class.
 *
 * @param self Ref to this module object. (Unued. Included to follow Python C extensions convention.)
 * @param args A tuple consisting of arguments passed to the function.
 *
 * @return Returns a Python capsule representing the pointer to ID graph head.
 **/
static PyObject *get_idgraph(PyObject *self, PyObject *args)
{
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj))
    {
        return NULL;
    }

    idGraphNodeList *visited = NULL;
    idGraphNode *head = create_id_graph(obj, visited);

    // TODO: free visited

    if (head == NULL)
    {
        PyErr_SetString(PyExc_Exception, "Could not generate ID Graph.");
        return NULL;
    }
    PyObject *id_graph_capsule = PyCapsule_New((void *)head, "idgraph", NULL);
    if (id_graph_capsule == NULL)
    {
        return NULL;
    }

    return id_graph_capsule;
}

/**
 * Returns the JSON representation of ID graph.
 *
 * This method is exposed to the Python caller class.
 *
 * @param self Ref to this module object. (Unued. Included to follow Python C extensions convention.)
 * @param args A tuple consisting of arguments passed to the function.
 *
 * @return Returns a Python string object i.e the JSON representation of the ID graph.
 **/
static PyObject *idgraph_json(PyObject *self, PyObject *args)
{
    if (self == NULL) {
        return NULL;
    }

    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj))
    {
        return NULL;
    }
    idGraphNode *head = (idGraphNode *)PyCapsule_GetPointer(obj, "idgraph");

    char *jsonRep = get_json_str(head);

    return PyUnicode_FromString(jsonRep);
}

/**
 * Compares two idGraphNode pointers.
 *
 * Recursively compares the id and type of an object and it's children.
 *
 * @param node1 idGraphNode pointer to be compared.
 * @param node2 idGraphNode pointer to be compared.
 *
 * @return Returns 1 if both the nodes are equivalent, else returns 0
 **/
int compareNodes(idGraphNode *node1, idGraphNode *node2)
{
    // Compare object type
    if (node1->obj_type != node2->obj_type)
    {
        return 0;
    }

    // Compare if primitive
    if (node1->is_primitive != node2->is_primitive)
    {
        return 0;
    }

    // If primitive
    if (node1->is_primitive)
    {
        // Compare for ints
        if (node1->obj_type == OBJ_TYPE_INT && node1->primitive.obj_int != node2->primitive.obj_int)
        {
            return 0;
        }
        // Compare for floats
        if (node1->obj_type == OBJ_TYPE_FLOAT && node1->primitive.obj_float != node2->primitive.obj_float)
        {
            return 0;
        }
        // Compare for boolean
        if (node1->obj_type == OBJ_TYPE_BOOL && node1->primitive.obj_bool != node2->primitive.obj_bool)
        {
            return 0;
        }
        // Compare for string
        if (node1->obj_type == OBJ_TYPE_STRING && strcmp(node1->primitive.obj_str, node2->primitive.obj_str) != 0)
        {
            return 0;
        }
    }
    else
    {
        // Compare object id
        if (node1->obj_id != node2->obj_id)
        {
            return 0;
        }
    }

    // Compare children
    idGraphNodeList *curr1 = node1->children;
    idGraphNodeList *curr2 = node2->children;
    while (curr1 != NULL && curr2 != NULL)
    {
        if (!compareNodes(curr1->child, curr2->child))
        {
            return 0;
        }
        curr1 = curr1->next;
        curr2 = curr2->next;
    }
    // If one of the lists is not empty, they are not equal
    if (curr1 != NULL || curr2 != NULL)
    {
        return 0;
    }
    return 1;
}

/**
 * Compares the ID graphs(idGraphNode *) for any 2 python capsule objects.
 *
 * This method is exposed to the Python caller class.
 *
 * @param self Ref to this module object. (Unued. Included to follow Python C extensions convention.)
 * @param args A tuple consisting of arguments passed to the function.
 *
 * @return Returns a Python boolean object indicating whether the objects are equal.
 * Returns True if equal, False otherwise.
 **/
static PyObject *idgraph_compare_object(PyObject *self, PyObject *args)
{
    PyObject *capsule1;
    PyObject *capsule2;
    if (!PyArg_ParseTuple(args, "OO", &capsule1, &capsule2))
    {
        return NULL;
    }

    void *ptr1 = PyCapsule_GetPointer(capsule1, "idgraph");
    void *ptr2 = PyCapsule_GetPointer(capsule2, "idgraph");

    if (ptr1 == NULL || ptr2 == NULL)
    {
        PyErr_SetString(PyExc_TypeError, "Invalid Capsule Object");
        return NULL;
    }
    idGraphNode *node1 = (idGraphNode *)ptr1;
    idGraphNode *node2 = (idGraphNode *)ptr2;
    if (node1 == NULL || node2 == NULL)
    {
        PyErr_SetString(PyExc_TypeError, "Invalid Capsule Object");
        return NULL;
    }
    int result = compareNodes(node1, node2);
    if (result == -1)
    {
        return NULL;
    }
    return PyBool_FromLong(result);
}

/**
 * Compares 2 python strings (String representation of the ID graph)
 *
 * This method is exposed to the Python caller class.
 *
 * @param self Ref to this module object. (Unued. Included to follow Python C extensions convention.)
 * @param args A tuple consisting of arguments passed to the function.
 *
 * @return Returns a Python boolean object indicating whether the strings are equal.
 **/
static PyObject *idgraph_compare_string(PyObject *self, PyObject *args)
{
    const char *str1, *str2;
    int result;

    if (!PyArg_ParseTuple(args, "ss", &str1, &str2))
    {
        return NULL;
    }

    result = strcmp(str1, str2);

    if (result == 0)
    {
        Py_RETURN_TRUE;
    }
    else
    {
        Py_RETURN_FALSE;
    }
}

/**
 * @brief Get the obj id object
 * 
 * @param self Unused.
 * @param args Python object for idGraphNode.
 * @return long The ID of the underlying object.
 */
static PyObject* idgraph_obj_id(PyObject* self, PyObject* args) 
{
    if (self == NULL)
    {
        return NULL;
    }

    PyObject *capsule;
    if (!PyArg_ParseTuple(args, "O", &capsule))
    {
        return NULL;
    }

    idGraphNode *node = (idGraphNode *) PyCapsule_GetPointer(capsule, "idgraph");
    if (node == NULL)
    {
        PyErr_SetString(PyExc_TypeError, "Invalid Capsule Object");
        return NULL;
    }

    return PyLong_FromLong(node->obj_id);
}

/**
 * An array of PyMethodDef structures that defines the methods of the idgraph module.
 **/
static PyMethodDef IdGraphMethods[] = {
    {"get_idgraph", get_idgraph, METH_VARARGS, "Python interface for the idgraph C library function."},
    {"idgraph_json", idgraph_json, METH_VARARGS, "Get JSON representation of the ID graph object."},
    {"compare_graph", idgraph_compare_object, METH_VARARGS, "Compare two capsule objects and return True if they are equal."},
    {"compare_json", idgraph_compare_string, METH_VARARGS, "Compare two JSON strings and return True if they are equal."},
    {"idgraph_obj_id", idgraph_obj_id, METH_VARARGS, "Get the object id of idGraphNode."},
    {NULL, NULL, 0, NULL}};

/**
 * A PyModuleDef structure that defines the idgraph module.
 * Contains the name of the module, a brief description of the module, and the methods of the module.
 **/
static struct PyModuleDef idgraphmodule = {
    PyModuleDef_HEAD_INIT,
    "c_idgraph",
    "Python interface for the idgraph C library function",
    -1,
    IdGraphMethods};

/**
 * Initializes the idgraph module.
 * It creates the Python module object and adds the idgraph function to it.
 *
 * @return The Python module object.
 *
 * @note This function is called automatically when the module is imported into a Python script.
 **/
PyMODINIT_FUNC PyInit_c_idgraph(void)
{
    return PyModule_Create(&idgraphmodule);
}
