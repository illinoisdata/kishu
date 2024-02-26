import VisitorModule
import pickle


class ObjectState:
    """
    Python interface for C implementation of visitor pattern for IdGraph and xxhash approach.
    obj: Object whose state needs to be hashed
    pick: Pickeld binaries of object
    hashed_state: Hashed state of the object obj
    traversal: Items hashed during object travsersal
    """

    def __init__(self, obj, include_traversal=False):
        self.pick = pickle.dumps(obj)

        self.hashed_state, self.traversal = VisitorModule.get_object_hash_and_trav_wrapper(
            obj, include_traversal)

    def compare_ObjectStates(self, other):
        """
        Input: other - ObjectState instance of another object (or same object with potentially
        different state)
        Compares both pickled binaries and hashed states
        """
        return self.pick == other.pick and self.hashed_state == other.hashed_state

    def update_object_hash(self, obj, include_traversal=False):
        """
        Inputs: obj - Object whose new state needs to be recorded
        Updates the hash and pickled bianries of the object state
        """
        self.pick = pickle.dumps(obj)
        self.hashed_state, self.traversal = VisitorModule.get_object_hash_and_trav_wrapper(
            obj, include_traversal)

    def get_object_hash(self):
        """
        Returns the current hash of the object state
        """
        return self.hashed_state

    # If not storing traversal, comment out this function
    def get_hashed_traversal(self):
        """
        Input: obj - Object whose state needs to be recorded
        Returns the data hashed during traversal
        """
        return self.traversal

    def id_set(self):
        return set([i for i in self.traversal if isinstance(i, int)])

    def is_overlap(self, other) -> bool:
        if self.id_set().intersection(other.id_set()):
            return True
        return False
