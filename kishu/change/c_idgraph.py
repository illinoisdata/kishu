
import time
import idgraph

def construct_fingerprint(obj, profile_dict) -> str:
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

    return id_graph_str

dic = {"A":1}
l = [1,2,dic]
profile = {}
dic["A"] = l
print(construct_fingerprint(l,profile))

m = set([1,2,3])
print(construct_fingerprint(m,profile))

a = (3,4)
l.append(a)

# l = [1,2,]
print(construct_fingerprint(l,profile))