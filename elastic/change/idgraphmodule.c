// Command to run this file
// C:\msys64\mingw64\bin\gcc.exe -fdiagnostics-color=always -g C:\Users\prana\elastic-notebook\elastic\change\idgraphmodule.c -o C:\Users\prana\elastic-notebook\elastic\change\idgraphmodule.exe -I\Users\prana\include

#define PY_SSIZE_T_CLEAN
#include <Python.h>

// Return a string rep of idGraph (each string should have id and obj type)

typedef struct idGraphNode {
    void* obj_id; // Pointer to memory address
    char* obj_type; // Type of object
    struct list* child_obj;
    int init;
} idGraphNode;



typedef struct list {
    struct idGraphNode* array;
    int size;
    int curr;
} list;

void add_node(idGraphNode node, list* myList){
    if(myList->size == 0){
        myList->array = (idGraphNode*) calloc(100, sizeof(idGraphNode));
        myList->size = 100;
    }
    if(myList->curr == myList->size-1){
        myList->array = realloc(myList->array, myList->size*sizeof(idGraphNode));
        myList->size = (myList->size)*2;
    }
    myList->array[myList->curr].obj_id = node.obj_id;
    myList->array[myList->curr].obj_type = node.obj_type;
    myList->array[myList->curr].child_obj = node.child_obj;
    (myList->curr)++;
}

struct idGraphNode get_node(void* id, list* visited){
    for(int i=0; i<=visited->curr; i++){
        if(visited->array[i].obj_id == id){
            return visited->array[i];
        }
    }
    idGraphNode n;
    n.init = 0;
    return n;
}

static struct idGraphNode iterate_object(PyObject *obj, list* visited, int nn){
    printf("n = ");
    printf("%d%s",nn,"\n");
    // PyObject *obj;
    // PyArg_ParseTuple(args, "O", &obj);
    printf("iterating the obj \n");
    if(PyList_Check(obj)) {
        printf("Object is a list\n");
    }
    // printf(obj);
    if (obj == NULL) {
        idGraphNode n;
        n.init = 0;
        return n;
    }
    
    idGraphNode node;

    // ToDo - Assign obj type to node
    // ToDo - Assign obj id to node
    // ToDo - Assign child objs to node
    
    // Assigned id of the object to node
    // node.obj_id = &obj;
    // Marked the node as visited
    add_node(node, visited);
    
    node.init = 1;
    
    // Checking exact type of the object in order to iterate it.
    if (PyList_Check(obj)) {
        // Setting object type
        node.obj_type = "list";
        // Process the list
        PyObject *iter;
        PyObject *item;
        if ((iter = PyObject_GetIter(obj)) == NULL) {
            printf("List is Empty.\n");
        }
        else{
            while ((item = PyIter_Next(iter)) != NULL) {
                if(PyList_Check(item)){
                    printf("Child is list\n");
                }
                if(PyList_Check(item) || PyTuple_Check(item) || PySet_Check(item) || PyDict_Check(item)){
                    // Check if id in visited
                    struct idGraphNode child_node = get_node(&obj, visited);
                    if (child_node.init != 0){
                        add_node(child_node,node.child_obj); 
                    }
                    else{
                        nn++;
                        add_node(iterate_object(item,visited,nn),node.child_obj);
                    }
                }
            }
        }
    }
    else{
        printf("Object is a NOT list\n");
    }

    return node;

}

static void idgraph_create(PyObject *self, PyObject *args){

    PyObject *obj;
    PyArg_ParseTuple(args, "O", &obj);
    if (PyList_Check(obj)) {
        printf("List found1\n");
    }

    list* visited;
    visited->array = (idGraphNode*) calloc(100, sizeof(idGraphNode));
    visited->size = 100;
    visited->curr = 0;

    // dict, list, tuple, set, (class instances), primitives(skip them)
    // Don't return as a byte string. we return the graph itself
    // Compare the graphs.

    idGraphNode head = iterate_object(obj, visited, 0);
    printf("head\n");
    printf(head.obj_id);
    printf(head.obj_type);
    printf(head.child_obj->curr);

    // if (PyUnicode_Check(obj)) {
    //     printf("Object is a string: %s\n", PyUnicode_AsUTF8(obj));
    // } else if (PyList_Check(obj)) {
    //     printf("Object is a list\n");
    //     // Process the list
    // } else if (PyDict_Check(obj)) {
    //     printf("Object is a dictionary\n");
    //     // Process the dictionary
    // } else if (PyTuple_Check(obj)){
    //     printf("Tuple object type\n");
    // } else if (PySet_Check(obj)){
    //     printf("Set object type\n");
    // }
    Py_RETURN_NONE;
    
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