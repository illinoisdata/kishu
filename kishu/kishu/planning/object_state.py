from kishu.planning.visitor import Visitor


def get_object_state(obj, visited: dict, visitor: Visitor, update_state=None, include_id=True):

    check, ret = visitor.check_visited(visited, id(obj), include_id)
    if check:
        return ret

    if isinstance(obj, (int, float, str, bool, type(None), type(NotImplemented), type(Ellipsis))):
        return visitor.visit_primitive(obj)

    elif isinstance(obj, tuple):
        return visitor.visit_tuple(obj, visited, include_id, update_state)

    elif isinstance(obj, list):
        return visitor.visit_list(obj, visited, include_id, update_state)

    elif isinstance(obj, set):
        return visitor.visit_set(obj, visited, include_id, update_state)

    elif isinstance(obj, dict):
        return visitor.visit_dict(obj, visited, include_id, update_state)

    elif isinstance(obj, (bytes, bytearray)):
        return visitor.visit_byte(obj, visited, include_id, update_state)

    elif isinstance(obj, type):
        return visitor.visit_type(obj, visited, include_id, update_state)

    elif callable(obj):
        return visitor.visit_callable(obj, visited, include_id, update_state)

    elif hasattr(obj, '__reduce_ex__'):
        return visitor.visit_custom_obj(obj, visited, include_id, update_state)

    else:
        return visitor.visit_other(obj, visited, include_id, update_state)
