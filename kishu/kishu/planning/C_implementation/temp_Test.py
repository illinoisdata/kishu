import VisitorModule

a = 5
b = VisitorModule.get_object_hash_wrapper(a)
c = VisitorModule.get_digest_hash_wrapper(b)
print(c)
