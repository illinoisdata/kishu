import VisitorModule
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
a = plt.plot(df['a'], df['b'])

# a = [1,2,3]
# a[1] = a

# x = lambda a : a + 10



# os.kill(PID, signal.SIGUSR1)
hw1 = VisitorModule.get_object_hash_wrapper(a)
hw2 = VisitorModule.get_object_hash_wrapper(a)

hash1 = VisitorModule.get_digest_hash_wrapper(hw1)
hash2 = VisitorModule.get_digest_hash_wrapper(hw2)

print(hash1 == hash2)
