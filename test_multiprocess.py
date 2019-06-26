"""
Demo code for intro of multi processing API
How to create a new child process.
Why do we need if __name___
"""
from multiprocessing import Process
import os

print("outer")

def info(title):
    print(title)
    print('module name:', __name__)
    if hasattr(os, 'getppid'):  # only available on Unix
        print('parent process:', os.getppid())
    print('process id:', os.getpid())

def f(name):
    info('function f')
    print('hello', name)

"""
if insures that the code inside this block is executed only when this script is run and not when the script is imported. 
Otherwise, any line in the script is executed also when the script is run and when the script is imported.
"""
if __name__ == '__main__':
    info('main line')
    p = Process(target=f, args=('bob',))
    p.start()
    p.join()