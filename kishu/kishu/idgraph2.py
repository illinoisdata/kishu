import hashlib
import pandas as pd
import pickle

class GraphNode:

    def __init__(self, id_obj = 0):
        self.id_obj = id_obj 
        self.children = []
        
def is_pickable(obj):
    try:
        if callable(obj):
            return False

        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, AttributeError, TypeError):
        return False


def get_object_state(obj, visited=None, include_id = True):
    if visited is None:
        visited = set()

    if hasattr(obj, "persistent_id"):
        print("-----------------------persistent_id-----------------")

    if id(obj) in visited:
        return "CYCLIC_REFERENCE"

    if isinstance(obj, (int, float, str, bool, type(None), type(NotImplemented), type(Ellipsis))):
        # return obj
        node = GraphNode()
        node.children.append(obj)
        return node

    elif isinstance(obj, tuple):
        node = GraphNode()
        for item in obj:
            child = get_object_state(item, visited, include_id)
            node.children.append(child)
        
        return node

    elif isinstance(obj, list):
        visited.add(id(obj))
        node = GraphNode()
        if include_id:
            node.id_obj = id(obj)
        
        for item in obj:
            child = get_object_state(item, visited, include_id)
            node.children.append(child)
        
        return node

    elif isinstance(obj, set):
        visited.add(id(obj))
        node = GraphNode(id_obj=id(obj))
        for item in sorted(obj):
            child = get_object_state(item, visited, include_id)
            node.children.append(child)
        return node


    elif isinstance(obj, dict):
        node = GraphNode()
        if include_id:
            node.id_obj = id(obj)
        
        for key, value in sorted(obj.items()):
            node.children.append(key)
            child = get_object_state(value, visited, include_id)
            node.children.append(child)
        
        return node
            
        

    elif isinstance(obj, (bytes, bytearray)):
        node = GraphNode()
        node.children.append(obj)
        return node

    elif isinstance(obj, type):
        node = GraphNode()
        node.children.append(str(obj))
        return node


    elif hasattr(obj, '__reduce_ex__'):
        if is_pickable(obj): 
            # if obj.__reduce_ex__(4) == obj.__reduce_ex__(4):
            visited.add(id(obj))
            reduced = obj.__reduce_ex__(4)
            node = GraphNode(id_obj=id(obj))

            if isinstance(reduced, str):
                node.children.append(reduced)
                return node
            
            # node.id_obj = id(obj)
            for item in reduced[1:]:
                child = get_object_state(item, visited, False)
                node.children.append(child)
            
            return node

    # If __reduce__
    elif hasattr(obj, '__reduce__'):
        if is_pickable(obj) and obj.__reduce__() == obj.__reduce__():
            visited.add(id(obj))
            reduced = obj.__reduce__()

            node = GraphNode(id_obj=id(obj))

            if isinstance(reduced, str):
                node.children.append(reduced)
                return node
            
            # node.id_obj = id(obj)
            for item in reduced[1:]:
                child = get_object_state(item, visited, False)
                node.children.append(child)
            
            return node


    elif hasattr(obj, '__dict__'):
        visited.add(id(obj))
        node = GraphNode()
        node.id_obj = id(obj)

        if hasattr(obj, '__getstate__'):
            if obj.__getstate__() == obj.__getstate__():
                
                for attr_name, attr_value in sorted(obj.__getstate__().items()):
                    node.children.append(attr_name)
                    child = get_object_state(attr_value, visited, False)
                    node.children.append(child)
                
                return node

        for attr_name, attr_value in sorted(obj.__dict__.items()):
            node.children.append(attr_name)
            child = get_object_state(attr_value, visited)
            node.children.append(child)
        
        return node

    else:
        node = GraphNode()
        node.children.append(str(obj))

def get_object_hash(obj):
    curr_state = get_object_state(obj)
    return hashlib.md5(str(curr_state).encode('utf-8')).hexdigest()


def convert_idgraph_to_list(node: GraphNode, ret_list):
    # pre oder
    if node.id_obj != 0:
        ret_list.append(node.id_obj)
    
    for child in node.children:
        if isinstance(child, GraphNode):
            convert_idgraph_to_list(child, ret_list)
        else:
            # print(child)
            ret_list.append(child)
        
def compare_idgraph(idGraph1: GraphNode, idGraph2: GraphNode) -> bool:
    ls1: list = []
    ls2: list = []

    convert_idgraph_to_list(idGraph1, ls1)
    convert_idgraph_to_list(idGraph2, ls2)

    if ls1 == ls2:
        return True
    else:
        return False


        