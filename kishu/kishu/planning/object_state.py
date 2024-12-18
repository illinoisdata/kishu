# regular imports
import xxhash

# kishu imports
import kishu.planning.hash_visitor as hash_visitor
import kishu.planning.idgraph_visitor as idgraph_visitor
from kishu.planning.visitor import Visitor


def create_idgraph(obj):
    vis1 = idgraph_visitor.idgraph()
    return get_object_state(obj, {}, vis1, None, True)


def create_hash(obj):
    vis1 = hash_visitor.hash_vis()
    x = xxhash.xxh32()
    return get_object_state(obj, set(), vis1, x, True)


def get_object_state(obj, visited, visitor: Visitor, hash_state=None, include_id=True):
    """
    Description: Get the state of the object, either as an idgraph or a xxhash object
    Inputs: obj - The object whose state needs to be captured
            visited - A dictionary containing visited objects
            visitor - A visitor object, either: idgraph or xxhash (not implemented yet)
            hash_state - Used for updating xxhash object each time a recursive call is
              made (not implemented yet). Not used in case of idgraph
            include_id - Flag to indicate whether to include id along with values in the object state
    Outputs: In case of idgraph visitor, the output is graph for the state of the object. Each node
                is a GraphNode. Return value is the root GraphNode of the graph
             In case of xxhash, the output is hash object which is recursively updated as it
                traverses the object. Return value is the xxhash object
    """
    ret = visitor.check_visited(visited, id(obj), type(obj), include_id, hash_state)
    if ret:
        return ret

    if isinstance(obj, (int, float, bool, str, type(None), type(NotImplemented), type(Ellipsis))):
        return visitor.visit_primitive(obj, hash_state)

    elif isinstance(obj, tuple):
        return visitor.visit_tuple(obj, visited, include_id, hash_state)

    elif isinstance(obj, list):
        return visitor.visit_list(obj, visited, include_id, hash_state)

    elif isinstance(obj, set):
        return visitor.visit_set(obj, visited, include_id, hash_state)

    elif isinstance(obj, dict):
        return visitor.visit_dict(obj, visited, include_id, hash_state)

    elif isinstance(obj, (bytes, bytearray)):
        return visitor.visit_byte(obj, visited, include_id, hash_state)

    elif isinstance(obj, type):
        return visitor.visit_type(obj, visited, include_id, hash_state)

    elif callable(obj):
        return visitor.visit_callable(obj, visited, include_id, hash_state)

    elif hasattr(obj, "__reduce_ex__"):
        return visitor.visit_custom_obj(obj, visited, include_id, hash_state)

    else:
        return visitor.visit_other(obj, visited, include_id, hash_state)
