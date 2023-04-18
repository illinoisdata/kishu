#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "cJSON.h"

// Forward declaration
typedef struct idGraphNode idGraphNode;  
idGraphNode *check_obj();

/**
 * A struct to represent a linkedlist node holding an idGraphNode.
 *
 * @member "next" Pointer to the next node.
 * @member "child" Pointer to the idGraphNode represented by the node.
 **/
typedef struct idGraphNodeList {
    struct idGraphNodeList* next;
    idGraphNode* child;
} idGraphNodeList;

/**
 * A struct to represent an ID Graph node.
 * @member "obj_id" Unique object id (memory address).
 * @member "obj_type" Type of object.
 * @member "children" Head of a linklist representing children of the object.
 **/
typedef struct idGraphNode {
    void* obj_id; // Pointer to memory address
    char* obj_type; // Type of object
    idGraphNodeList* children;
} idGraphNode;

/**
 * Constructs a string representation of the ID Graph (idGraphNode *).
 *
 * Recursively iterates over the ID graph and creates a string representation.
 * Format of the string - " `object_type` (`object_id`) -> "
 *
 * @param node Head node of the ID graph.
 *
 * @return Returns the computed string.
 **/
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

/**
 * Constructs a cJSON object representation of the ID Graph (idGraphNode *).
 *
 * Recursively iterates over the ID graph and creates a JSON object.
 *
 * @param node Head node of the ID graph.
 *
 * @return Returns the computed cJSON object.
 **/
cJSON *get_json_rep(idGraphNode* node){
    
    cJSON *node_obj = cJSON_CreateObject(); 

    // Add the object id and type as JSON string values

    // Allocate memory for the string representation of obj_id
    size_t id_size = snprintf(NULL, 0, "%p", node->obj_id);
    int len = id_size;
    char* obj_id = malloc(len * sizeof(char));
    snprintf(obj_id, len,"%p",node->obj_id);

    cJSON_AddStringToObject(node_obj, "obj_id", obj_id);
    cJSON_AddStringToObject(node_obj, "obj_type", node->obj_type);
    
    cJSON* children_array = cJSON_CreateArray();
    cJSON_AddItemToObject(node_obj, "children", children_array);
    idGraphNodeList* child_node = node->children;
    while (child_node != NULL) {
        cJSON_AddItemToArray(children_array, get_json_rep(child_node->child));
        child_node = child_node->next;
    }
    return node_obj;
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
char* get_json_str(idGraphNode* node){
    cJSON* jsonRep = get_json_rep(node);
    char* jsonString = cJSON_Print(jsonRep);
    cJSON_Delete(jsonRep);
    return jsonString;
}

/**
 * Adds a child idGraphNode to a parent idGraphNode.
 *
 * @param parent Parent node.
 * @param child Child node.
 **/
void add_child(idGraphNode* parent, idGraphNode* child) {
    idGraphNodeList* new_node = (idGraphNodeList*) malloc(sizeof(idGraphNodeList));
    new_node->child = child;
    new_node->next = parent->children;
    parent->children = new_node;
}

/**
 * Serches for an ID graph node in a linkedlist.
 *
 * @param list The idGraphNodeList to search in.
 * @param id The id of the idGraphNode being serched.
 *
 * @return Returns the the ID graph node(idGraphNode *) if exists
 * else returns NULL
 **/
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

/**
 * Adds an ID graph node to the visited list.
 *
 * @param visited The idGraphNodeList.
 * @param node The node to be added to viited list.
 **/
idGraphNodeList *mark_visited(idGraphNodeList *visited, idGraphNode* node) {
    idGraphNodeList* new_node = malloc(sizeof(idGraphNodeList));
    new_node->next = visited;
    new_node->child = node;
    return new_node;
}

idGraphNode* create_idGraphNode(void* obj_id, char* obj_type) {
    idGraphNode* node = (idGraphNode*) malloc(sizeof(idGraphNode));
    node->obj_id = obj_id;
    node->obj_type = obj_type;
    node->children = NULL;
    return node;
}

void process_collection_items(PyObject* obj, idGraphNode* node, idGraphNodeList* visited) {
    Py_ssize_t size = PySequence_Size(obj);
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *item = PySequence_GetItem(obj, i);
        void *id = (void*)&(*item);
        idGraphNode *child = find_idGraphNode_in_list(visited, id);
        if(child == NULL){
            child = check_obj(item, visited);
        }
        else{
            child = create_idGraphNode(child->obj_id, child->obj_type);
        }
        if(child != NULL){
            add_child(node,child);
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
 * @param obj A python object.
 * @param visited A list of visited objects.
 *
 * @return Returns the head of the ID graph (idGraphNode *)
 **/
idGraphNode *check_obj(PyObject *obj, idGraphNodeList *visited) {
    idGraphNode* node = NULL;
    // List
    if (PyList_Check(obj)) {
        // printf("List\n");
        node = create_idGraphNode((void*)&(*obj), "list");
        visited = mark_visited(visited, node);
        process_collection_items(obj, node, visited);
    }
    // Tuple
    else if (PyTuple_Check(obj)) {
        node = create_idGraphNode((void*)&(*obj), "tuple");
        visited = mark_visited(visited, node);
        process_collection_items(obj, node, visited);
    }
    // Dictionary
    else if (PyDict_Check(obj)) {
        // printf("Dict\n");
        node = create_idGraphNode((void*)&(*obj), "dictionary");
        visited = mark_visited(visited, node);
        PyObject *keys = PyDict_Keys(obj);
        PyObject *values = PyDict_Values(obj);
        Py_ssize_t size = PyList_Size(keys);
        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject *key = PyList_GetItem(keys, i);
            PyObject *value = PyList_GetItem(values, i);
            // Processing key
            void *id = (void*)&(*key);
            idGraphNode *child = find_idGraphNode_in_list(visited, id);
            if(child == NULL){
                child = check_obj(key, visited);
            }
            else{
                idGraphNode *visited_child = (idGraphNode*) malloc(sizeof(idGraphNode));
                visited_child->obj_id = child->obj_id;
                visited_child->obj_type = child->obj_type;
                visited_child->children = NULL;
                child = visited_child;
            }
            if(child != NULL){
                add_child(node,child);
            }
            // Processing value
            id = (void*)&(*value);
            child = find_idGraphNode_in_list(visited, id);
            if(child == NULL){
                printf("Dict's Child NULL\n");
                child = check_obj(value, visited);
            }
            else{
                idGraphNode *visited_child = (idGraphNode*) malloc(sizeof(idGraphNode));
                visited_child->obj_id = child->obj_id;
                visited_child->obj_type = child->obj_type;
                visited_child->children = NULL;
                child = visited_child;
            }
            if(child != NULL){
                add_child(node,child);
            }
        }
    }
    // Set
    else if (PyAnySet_Check(obj)) {
        node = create_idGraphNode((void*)&(*obj), "set");
        visited = mark_visited(visited, node);

        // process_collection_items(obj, node, visited);
        PyObject *iter = PyObject_GetIter(obj);
        PyObject *item;
        while ((item = PyIter_Next(iter))) {
            void *id = (void*)&(*item);
            idGraphNode *child = find_idGraphNode_in_list(visited, id);
            if(child == NULL){
                child = check_obj(item, visited);
            }
            else{
                idGraphNode *visited_child = (idGraphNode*) malloc(sizeof(idGraphNode));
                visited_child->obj_id = child->obj_id;
                visited_child->obj_type = child->obj_type;
                visited_child->children = NULL;
                child = visited_child;
            }
            if(child != NULL){
                add_child(node,child);
            }
        }
    }
    // Class object with __dict__ attribute
    else if (!PyModule_Check(obj) 
            && PyObject_HasAttrString(obj, "__dict__") 
            && !PyType_Check(obj)){
        node = create_idGraphNode((void*)&(*obj), "class obj");
        visited = mark_visited(visited, node);
        PyObject *dict = PyObject_GetAttrString(obj, "__dict__");
        if (dict != NULL && PyDict_Check(dict)) {
            Py_ssize_t pos = 0;
            PyObject *key, *value;
            while (PyDict_Next(dict, &pos, &key, &value)) {
                if (PyUnicode_Check(key)) {
                    const char *name = PyUnicode_AsUTF8(key);
                    if (name != NULL && name[0] != '_') {
                        void *id = (void*)value;
                        idGraphNode *child = find_idGraphNode_in_list(visited, id);
                        if (child == NULL) {
                            child = check_obj(value, visited);
                        }
                        else{
                            idGraphNode *visited_child = (idGraphNode*) malloc(sizeof(idGraphNode));
                            visited_child->obj_id = child->obj_id;
                            visited_child->obj_type = child->obj_type;
                            visited_child->children = NULL;
                            child = visited_child;
                        }
                        if (child != NULL) {
                            add_child(node, child);
                        }
                    }
                }
            }
        }
    }
    
    // Else it's a primitive so you ignore it
    return node;
}

/**
 * Gets the ID graph(idGraphNode *) for any python object.
 *
 * This method is exposed to the Python caller class.
 *
 * @param self Ref to this module object. (Unued. Included to follow Python C extensions convention.)
 * @param args A tuple consisting of arguments passed to the function.
 *
 * @return Returns a Python string object repreenting the ID graph.
 **/
static PyObject *idgraph_create(PyObject *self, PyObject *args) {
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }
    
    idGraphNodeList* visited = NULL;
    idGraphNode *head = check_obj(obj, visited);

    // char *stringRep = get_string_rep(head);
    // return Py_BuildValue("s", stringRep);

    char* jsonString = get_json_str(head);
    return Py_BuildValue("s", jsonString);
}

/**
 * An array of PyMethodDef structures that defines the methods of the idgraph module.
 **/
static PyMethodDef IdGraphMethods[] = {
    {"idgraph", idgraph_create, METH_VARARGS, "Python interface for the idgraph C library function"},
    {NULL, NULL, 0, NULL}
};

/**
 * A PyModuleDef structure that defines the idgraph module.
 * Contains the name of the module, a brief description of the module, and the methods of the module.
 **/
static struct PyModuleDef idgrapgmodule = {
    PyModuleDef_HEAD_INIT,
    "idgraph",
    "Python interface for the idgraph C library function",
    -1,
    IdGraphMethods
};

/**
 * Initializes the idgraph module. 
 * It creates the Python module object and adds the idgraph function to it.
 * 
 * @return The Python module object.
 *
 * @note This function is called automatically when the module is imported into a Python script.
 **/
PyMODINIT_FUNC PyInit_idgraph(void) {
    return PyModule_Create(&idgrapgmodule);
}