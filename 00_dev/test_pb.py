#! /usr/bin/env python3
# coding: utf-8

import tqdm
import sys
from time import sleep

# Emulate terminal in output console > Configuration

if __name__ == '__main__':
    for x in tqdm.tqdm(range(3), desc='loop 1', leave=False, file=sys.stdout, ascii=True):
        sleep(0.5)
        for z in tqdm.tqdm(range(20), desc='loop 2', leave=False, file=sys.stdout, ascii=True):
            sleep(0.3)
    print("over")
