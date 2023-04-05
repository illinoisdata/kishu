from c_idgraph import construct_fingerprint


a = [2,3]
b = ["string"]
myObj = [1,a,b,b]

profile_dict = {}

print(id(myObj))

print(construct_fingerprint(myObj,profile_dict))

c = (4,4)
myObj[1] = c

print(construct_fingerprint(myObj,profile_dict))

myObj[1] = a
print(construct_fingerprint(myObj,profile_dict))
