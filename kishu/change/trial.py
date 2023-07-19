import hashlib
import pandas as pd
import pickle

def is_pickable(obj):
    try:
        if callable(obj):
            return False

        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, AttributeError, TypeError):
        return False
    

def get_object_state(obj, visited=None):
    if visited is None:
        visited = set()

    if hasattr(obj, "persistent_id"):
        print(obj, type(obj))

    if id(obj) in visited:
        return "CYCLIC_REFERENCE"

    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    
    elif isinstance(obj, tuple):
        visited.add(id(obj))
        state_representation = []
        for item in obj:
            item_state = get_object_state(item, visited)
            state_representation.append(item_state)
        return tuple(state_representation)

    elif isinstance(obj, list):
        visited.add(id(obj))
        state_representation = []
        for item in obj:
            item_state = get_object_state(item, visited)
            state_representation.append(item_state)
        return tuple(state_representation)
        # return tuple(get_object_state(item, visited | {id(obj)}) for item in obj)

    elif isinstance(obj, set):
        visited.add(id(obj))
        state_representation = []
        for item in sorted(obj):
            item_state = get_object_state(item, visited)
            state_representation.append(item_state)
        return tuple(state_representation)    
    
    elif isinstance(obj, dict):
        # visited.add(id(obj))
        # dict_inst = dict(sorted(obj.copy().items()))
        dict_inst = {}
        for key, value in sorted(obj.items()):
            dict_inst[key] = get_object_state(value, visited)
        
        return dict_inst
    
    elif isinstance(obj, (bytes, bytearray)):
        return obj

    elif isinstance(obj, type):
        return str(obj)
    
    elif hasattr(obj, '__reduce_ex__'):
            if is_pickable(obj) and obj.__reduce_ex__(4) == obj.__reduce_ex__(4):
                visited.add(id(obj))
                reduced = obj.__reduce_ex__(4)

                if isinstance(reduced, str):
                    return reduced
                
                state_representation = []
                for item in reduced[1:]:
                    item_state = get_object_state(item, visited)
                    state_representation.append(item_state)
                
                return tuple(state_representation)

    # If __reduce__
    elif hasattr(obj, '__reduce__'):
        if is_pickable(obj) and obj.__reduce__() == obj.__reduce__():
            visited.add(id(obj))
            reduced = obj.__reduce__()

            if isinstance(reduced, str):
                return reduced
            
            state_representation = []
            for item in reduced[1:]:
                item_state = get_object_state(item, visited)
                state_representation.append(item_state)
            
            return tuple(state_representation)




    elif hasattr(obj, '__dict__'):

        if hasattr(obj, '__getstate__'):
            if obj.__getstate__() == obj.__getstate__():
                # obj_dict =  dict(sorted(obj.__getstate__().items()))
                obj_dict = {}
                for attr_name, attr_value in sorted(obj.__getstate__().items()):
                    obj_dict[attr_name] = get_object_state(attr_value, visited)
                
                return obj_dict
            
        # Use __dict__ only
        # obj_dict = obj.__dict__.copy()
        obj_dict = {}
        for attr_name, attr_value in sorted(obj.__dict__.items()):
            obj_dict[attr_name] = get_object_state(attr_value, visited)
        
        return obj_dict

    else:
        return str(obj)

def get_object_hash(obj):
    curr_state = get_object_state(obj)
    return hashlib.md5(str(curr_state).encode('utf-8')).hexdigest()
