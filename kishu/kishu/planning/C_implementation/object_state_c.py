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
        self.hashed_state, self.traversal = VisitorModule.get_object_hash_and_trav_wrapper(
            obj)
        # self.visitor = VisitorModule.get_visitor_wrapper(obj)
        # self.hashed_state = VisitorModule.get_digest_hash_wrapper(self.visitor)
        # self.traversal = VisitorModule.get_visited_objs_wrapper(self.visitor)

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
        Inputs: obj - Object whose state needs to be recorded
        Updates the hash and pickled bianries of the object state
        """
        self.pick = pickle.dumps(obj)
        # self.visitor = VisitorModule.get_visitor_wrapper(obj)
        # self.hashed_state = VisitorModule.get_digest_hash_wrapper(self.visitor)
        self.hashed_state, self.traversal = VisitorModule.get_object_hash_and_trav_wrapper(
            obj)

    def get_object_hash(self):
        """
        Returns the current hash of the object state
        """
        return self.hashed_state

    # def get_visitor(self):
    #     """
    #     Inputs: obj - Object whose state needs to be recorded
    #     Returns a PyCaspsule object for the XXH32_hash object
    #     """
    #     return self.visitor

    def get_hashed_traversal(self):
        """
        Input: obj - Object whose state needs to be recorded
        Returns the data hashed during traversal
        """
        return self.traversal
