import hashlib
import pandas
import pickle

class GraphNode:

    def __init__(self, id_obj = 0, check_value_only = False):
        self.id_obj = id_obj 
        self.children = []
        self.check_value_only = check_value_only
    
    def __eq__(self, other):
        return compare_idgraph(self, other)
        
def is_pickable(obj):
    try:
        if callable(obj):
            return False

        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, AttributeError, TypeError):
        return False

def get_object_state(obj, visited=None, include_id = True) -> GraphNode:
    if visited is None:
        visited = set()

    if id(obj) in visited:
        node = GraphNode(check_value_only=True)
        node.children.append("CYCLIC_REFERENCE")
        return node

    if isinstance(obj, (int, float, str, bool, type(None), type(NotImplemented), type(Ellipsis))):
        # return obj
        node = GraphNode(check_value_only=True)
        node.children.append(obj)
        return node

    elif isinstance(obj, tuple):
        node = GraphNode(check_value_only=True)
        for item in obj:
            child = get_object_state(item, visited, include_id)
            node.children.append(child)
        return node

    elif isinstance(obj, list):
        visited.add(id(obj))
        node = GraphNode(check_value_only = True)
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        
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
        node = GraphNode(check_value_only=True)
        if include_id:
            node.id_obj = id(obj)
            node.check_value_only = False
        
        for key, value in sorted(obj.items()):
            node.children.append(key)
            child = get_object_state(value, visited, include_id)
            node.children.append(child)
        return node
               
    elif isinstance(obj, (bytes, bytearray)):
        node = GraphNode(check_value_only=True)
        node.children.append(obj)
        return node

    elif isinstance(obj, type):
        node = GraphNode(check_value_only=True)
        node.children.append(str(obj))
        return node

    elif hasattr(obj, '__reduce_ex__'):
        if is_pickable(obj): 
            # if obj.__reduce_ex__(4) == obj.__reduce_ex__(4):
            visited.add(id(obj))
            reduced = obj.__reduce_ex__(4)
            node = GraphNode(check_value_only=True)
            if not isinstance(obj, pandas.core.indexes.range.RangeIndex):
                node.id_obj = id(obj)
                node.check_value_only = False

            if isinstance(reduced, str):
                node.children.append(reduced)
                return node
            
            # node.id_obj = id(obj)
            for item in reduced[1:]:
                child = get_object_state(item, visited, False)
                node.children.append(child)
            
            return node

    elif hasattr(obj, '__reduce__'):
        # if is_pickable(obj) and obj.__reduce__() == obj.__reduce__():
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
        node = GraphNode(check_value_only=True)
        node.children.append(str(obj))
        return node

def get_object_hash(obj):
    curr_state = get_object_state(obj)
    return hashlib.md5(str(curr_state).encode('utf-8')).hexdigest()

def convert_idgraph_to_list(node: GraphNode, ret_list):
    # pre oder
    if not node.check_value_only:
        ret_list.append(node.id_obj)
    
    for child in node.children:
        if isinstance(child, GraphNode):
            convert_idgraph_to_list(child, ret_list)
        else:
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