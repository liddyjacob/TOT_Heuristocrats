
import os
import time
from multiprocessing import Process


def func():
    if os.fork() != 0:  # <--
        return          # <--
    print('sub process is running')
    time.sleep(5)
    print('sub process finished')


if __name__ == '__main__':
    p = Process(target=func)
    p.start()
    p.join()
    print('done')