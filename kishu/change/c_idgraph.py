import time
import idgraph
import json

def construct_fingerprint(obj: any, profile_dict: dict) -> any:
    """
        Returns a json representation of the ID graph for a python object.

        Parameters:
        obj (any): Any python object 
        profile_dict (dictionary): A python dictionary

        Returns:
        str: Json representation of ID graph
    """

    # Capturing time taken yo generate id graph
    start = time.time()

    # Calling "C" function to generate id graph
    id_graph_str = idgraph.idgraph(obj) # Call to the C function

    # Capturing time
    end = time.time()
    profile_dict["idgraph"] = end - start

    return json.loads(id_graph_str)

def pretty_json(myJson: any):
    return json.dumps(myJson, indent=2)