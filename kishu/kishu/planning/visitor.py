from abc import ABC, abstractmethod


class Visitor(ABC):
    """
    Class to provide visitor pattern to an algorithm attempting to capture the state of an object.
    Each function is designed to handle different types of objects.
    """

    @abstractmethod
    def check_visited(self, visited, obj_id, obj_type, include_id, hash_state):
        pass

    @abstractmethod
    def visit_primitive(self, obj, hash_state):
        pass

    @abstractmethod
    def visit_tuple(self, obj, visited, include_id, hash_state):
        pass

    @abstractmethod
    def visit_list(self, obj, visited, include_id, hash_state):
        pass

    @abstractmethod
    def visit_set(self, obj, visited, include_id, hash_state):
        pass

    @abstractmethod
    def visit_dict(self, obj, visited, include_id, hash_state):
        pass

    @abstractmethod
    def visit_byte(self, obj, visited, include_id, hash_state):
        pass

    @abstractmethod
    def visit_type(self, obj, visited, include_id, hash_state):
        pass

    @abstractmethod
    def visit_callable(self, obj, visited, include_id, hash_state):
        pass

    @abstractmethod
    def visit_custom_obj(self, obj, visited, include_id, hash_state):
        pass

    @abstractmethod
    def visit_other(self, obj, visited, include_id, hash_state):
        pass
