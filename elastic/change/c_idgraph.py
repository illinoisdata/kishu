import idgraph
import pandas as pd

class Test:

    def __init__(self):
        pass

data = {
  "calories": [420, 380, 390],
  "duration": [50, 40, 45]
}

a = [1,2,3]
myObj = [5,a]

print(myObj)
idgraph.idgraph(myObj)
