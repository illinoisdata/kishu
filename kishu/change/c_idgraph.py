
import time
import idgraph

def construct_fingerprint(obj, profile_dict) -> str:
    """
        A fingerprint of the object consists of its ID graph.
        This function returns a string representation of the ID graph.
    """
    start = time.time()
    id_graph_str = idgraph.idgraph(obj) # Call to the C function
    end = time.time()
    profile_dict["idgraph"] = end - start

    return id_graph_str




