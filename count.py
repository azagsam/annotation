import re

texts = 0
tokens = 0
with open('data/ccmaks/ccmaks4list.vert/ccmaks4list.vert', 'r') as f:
    for line in f:
        if line.startswith('<text id'):
            texts += 1
        if not re.search('<.*>', line):
            tokens += 1
print('ccMaks', f'Num of texts: {texts}', f'Num of tokens: {tokens}')

texts = 0
tokens = 0
with open('data/ccucbeniki/ccucbeniki4list.vert/ccucbeniki4list.vert', 'r') as f:
    for line in f:
        if line.startswith('<text id'):
            texts += 1
        if not re.search('<.*>', line):
            tokens += 1
print('ccUcbeniki', f'Num of texts: {texts}', f'Num of tokens: {tokens}')