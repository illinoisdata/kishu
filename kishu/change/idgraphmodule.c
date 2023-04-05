// Command to run this file
// C:\msys64\mingw64\bin\gcc.exe -fdiagnostics-color=always -g C:\Users\prana\elastic-notebook\kishu\change\idgraphmodule.c -o C:\Users\prana\elastic-notebook\elastic\change\idgraphmodule.exe -I\Users\prana\include

#define PY_SSIZE_T_CLEAN
#include <Python.h>

// Return a string rep of idGraph (each string should have id and obj type)

typedef struct idGraphNode idGraphNode;  // Forward declaration
char *get_string_rep(idGraphNode *head);

typedef struct idGraphNodeList {
    struct idGraphNodeList* next;
    idGraphNode* child;
} idGraphNodeList;

typedef struct idGraphNode {
    void* obj_id; // Pointer to memory address
    char* obj_type; // Type of object
    idGraphNodeList* children;
} idGraphNode;

char *get_string_rep(idGraphNode* node) {
    if(node == NULL){
        return "";
    }
    // allocate memory for the string representation
    size_t id_size = snprintf(NULL, 0, "%p", node->obj_id);
    int len = strlen(node->obj_type) + id_size + 10;
    char* str = malloc(len * sizeof(char));
    snprintf(str, len,"%s (%p)", node->obj_type, node->obj_id);
    // recursively print the children
    idGraphNodeList* current = node->children;
    char* child_str;
    while (current != NULL) {
        child_str = get_string_rep(current->child);
        len += strlen(child_str) + 5;
        str = realloc(str, len * sizeof(char));
        strcat(str, " -> ");
        strcat(str, child_str);
        free(child_str);
        current = current->next;
    }
    return str;
}

void add_child(idGraphNode* parent, idGraphNode* child) {
    idGraphNodeList* new_node = (idGraphNodeList*) malloc(sizeof(idGraphNodeList));
    new_node->child = child;
    new_node->next = parent->children;
    parent->children = new_node;
}

idGraphNode *find_idGraphNode_in_list(idGraphNodeList* list, void *id) {
    idGraphNodeList* current = list;
    while (current != NULL) {
        if (current->child->obj_id == id) {
            return current->child;
        }
        current = current->next;
    }
    return NULL;
}

void mark_visited(idGraphNodeList *visited, idGraphNode* node) {
    idGraphNodeList* new_node = malloc(sizeof(idGraphNodeList));
    new_node->next = visited;
    new_node->child = node;
    visited = new_node;
}

idGraphNode *check_obj(PyObject *obj, idGraphNodeList *visited) {

    idGraphNode* node = NULL;

    // Identifying type of obj and processing it recursively

    // List
    if (PyList_Check(obj)) {
        node = (idGraphNode*) malloc(sizeof(idGraphNode));
        node->obj_id = (void*)&(*obj);
        node->obj_type = "list";
        node->children = NULL;
        mark_visited(visited, node);
        Py_ssize_t size = PyList_Size(obj);
        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject *item = PyList_GetItem(obj, i);
            void *id = (void*)&(*item);
            idGraphNode *child = find_idGraphNode_in_list(visited, id);
            if(child == NULL){
                child = check_obj(item, visited);
            }
            if(child != NULL){
                add_child(node,child);
            }
            // Py_DECREF(item);
        }
    }
    // Tuple
    else if (PyTuple_Check(obj)) {
        node = (idGraphNode*) malloc(sizeof(idGraphNode));
        node->obj_id = (void*)&(*obj);
        node->obj_type = "tuple";
        node->children = NULL;
        mark_visited(visited, node);
        Py_ssize_t size = PyTuple_Size(obj);
        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject *item = PyTuple_GetItem(obj, i);
            void *id = (void*)&(*item);
            idGraphNode *child = find_idGraphNode_in_list(visited, id);
            if(child == NULL){
                child = check_obj(item, visited);
            }
            if(child != NULL){
                add_child(node,child);
            }
            // Py_DECREF(item);
        }
    }
    // ToDo - Dictionary
    // else if (PyDict_Check(obj)) {
    //     printf("dict\n");
    //     PyObject *keys = PyDict_Keys(obj);
    //     PyObject *values = PyDict_Values(obj);
    //     Py_ssize_t size = PyList_Size(keys);
    //     for (Py_ssize_t i = 0; i < size; i++) {
    //         PyObject *key = PyList_GetItem(keys, i);
    //         PyObject *value = PyList_GetItem(values, i);
    //         if (check_obj(key, visited) == 1 || check_obj(value, visited) == 1) {
    //             return 1;
    //         }
    //     }
    // }
    // ToDo - Set
    // else if (PyAnySet_Check(obj)) {
    //     printf("Set\n");
    //     Py_ssize_t set_size = PySet_Size(obj);
    //     // PyObject *setArr[set_size];
    //     for (Py_ssize_t i = 0; i < set_size; i++) {
    //         PyObject *item = PySet_Pop(obj);
    //         setArr[i] = item;
    //         check_obj(item, visited);
    //     }
    // }
    // ToDo - Any other iterable object with __dict__ attribute
    // else if (PyObject_HasAttrString(obj, "__dict__")){
    //     printf("has __dict__\n");
    //     return 0;
    // }
    
    // Else it's a primitive so you ignore it
    return node;
}

static PyObject *idgraph_create(PyObject *self, PyObject *args) {
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }
    idGraphNodeList* visited = NULL;
    idGraphNode *head = check_obj(obj, visited);
    char *stringRep = get_string_rep(head);
    return Py_BuildValue("s", stringRep);
}

static PyMethodDef IdGraphMethods[] = {
    {"idgraph", idgraph_create, METH_VARARGS, "Python interface for the idgraph C library function"},
    {NULL, NULL, 0, NULL}
};


static struct PyModuleDef idgrapgmodule = {
    PyModuleDef_HEAD_INIT,
    "idgraph",
    "Python interface for the idgraph C library function",
    -1,
    IdGraphMethods
};

PyMODINIT_FUNC PyInit_idgraph(void) {
    return PyModule_Create(&idgrapgmodule);
}