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

    def __init__(self, obj):
        self.pick = pickle.dumps(obj)

        # If using get_object_hash_wrapper(), comment this line.
        # If using get_object_hash_and_trav_wrapper(), uncomment this line
        # self.hashed_state, self.traversal = VisitorModule.get_object_hash_and_trav_wrapper(
        #     obj)

        # If using get_object_hash_and_trav_wrapper(), comment this line
        # If using get_object_hash_wrapper(), uncomment this line.
        self.hashed_state = VisitorModule.get_object_hash_wrapper(obj)

    # def compare_obj_hash(self, obj):
    #     """
    #     Input: obj - Object whose state needs to be recorded
    #     Checks whether hashed state of obj changes on two successive runs on the same object
    #     """
    #     if pickle.dumps(obj) != pickle.dumps(obj):
    #         return False
    #     else:
    #         return self.get_object_hash(obj) == self.get_object_hash(obj)

    def compare_ObjectStates(self, other):
        """
        Input: other - ObjectState instance of another object (or same object with potentially
        different state)
        Compares both pickled binaries and hashed states
        """
        return self.pick == other.pick and self.hashed_state == other.hashed_state

    def update_object_hash(self, obj):
        """
        Inputs: obj - Object whose new state needs to be recorded
        Updates the hash and pickled bianries of the object state
        """
        self.pick = pickle.dumps(obj)

        # If storing traversal as well, uncomment this line, otherwise comment out
        # self.hashed_state, self.traversal = VisitorModule.get_object_hash_and_trav_wrapper(
        #     obj)

        # If only storing hashed state, uncomment this line, otherwise comment out
        self.hashed_state = VisitorModule.get_object_hash_wrapper(obj)

    def get_object_hash(self):
        """
        Returns the current hash of the object state
        """
        return self.hashed_state

    # If storing traversal, uncomment this function
    # def get_hashed_traversal(self):
    #     """
    #     Input: obj - Object whose state needs to be recorded
    #     Returns the data hashed during traversal
    #     """
    #     return self.traversal
