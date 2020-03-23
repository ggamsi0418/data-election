import pickle
import os

filename = 'sample.py'

with open(filename) as file_object:
    contents = file_object.read()
    print(contents)
    bytes_object = pickle.dumps(contents, protocol=5)
    print(bytes_object)
    un_bytes_object = pickle.loads(bytes_object)
    print(un_bytes_object)

# pyFile = open('sample.py', 'rb')
# print(pyFile)
# SIZE = os.path.getsize('sample.py')
# print(SIZE)
