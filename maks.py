import os

import json
from conllu import parse
from tqdm import tqdm
import classla
from collections import defaultdict
import numpy as np


def conllu2txt(source, output):
    # fetch document
    for src_file in tqdm(os.listdir(source)):
        if src_file in list(os.listdir(output)):
            continue
        doc_id = src_file.split('.')[0]
        src_path = os.path.join(source, src_file)

        # parse document
        parsed_text = ""
        with open(src_path, 'r', encoding="utf-8") as f:
            sentences = parse(f.read())
            for sent in sentences:
                text = sent.metadata['text']
                if not parsed_text:
                    parsed_text += text
                elif 'newpar id' in sent.metadata.keys():
                    parsed_text += '\n\n' + text
                else:
                    parsed_text += ' ' + text

        # write txt
        out_path = os.path.join(output, doc_id + '.txt')
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write(parsed_text)


def old2new(source, output):
    # fetch document
    for src_file in tqdm(os.listdir(source)):
        if src_file in list(os.listdir(output)):
            continue
        doc_id = src_file.split('.')[0]
        src_path = os.path.join(source, src_file)

        # parse document
        parsed_text = ""
        with open(src_path, 'r', encoding="utf-8") as f:
            sentences = parse(f.read())
            for sent in sentences:
                text = sent.metadata['text']
                if not parsed_text:
                    parsed_text += text
                elif 'newpar id' in sent.metadata.keys():
                    parsed_text += '\n\n' + text
                else:
                    parsed_text += ' ' + text

        # annotate, wrap with exception for out of memory problems
        try:
            doc = nlp(parsed_text)
            # prepare for output (prepend with "maks")
            classla_out = doc.to_conll()
            maks_out = ""
            for line in classla_out.splitlines():
                if line.startswith('# newpar id') or line.startswith('# sent_id'):
                    key, value = line.split(' = ')
                    new_line = f"{key} = {doc_id}.{value}"
                    maks_out += new_line + "\n"
                else:
                    maks_out += line + '\n'
            maks_out = f"# newdoc id = {doc_id}\n" + maks_out

            # write
            out_path = os.path.join(output, doc_id + '.conllu')
            with open(out_path, 'w', encoding='utf-8') as out:
                out.write(maks_out)

        except RuntimeError as e:
            if str(e).startswith('CUDA out of memory.'):
                with open('failed-maks.txt', 'a') as f:
                    f.write(src_file)
                    f.write('\n')
            else:
                print('Other type of error')


def reduce_doc_size(source, target):
    # count tokens in each document
    counter = defaultdict(int)
    with open(source, 'r') as f:
        for line in tqdm(f):
            if line.startswith('<text id'):
                doc_id = line.split()[1].split('=')[1][1:-1]
            elif len(line.split('\t')) == 10:
                counter[doc_id] += 1
    reduced_sizes = {doc: int(np.ceil(x * 0.1)) for doc, x in counter.items()}  # 10% of each document

    # find sent_ids that exceed reduced sizes
    sent_ids = {}
    with open(source, 'r') as f:
        for line in tqdm(f):
            if line.startswith('<text id'):
                n = 0
                doc_id = line.split()[1].split('=')[1][1:-1]
            elif len(line.split('\t')) == 10:
                n += 1
                if n > reduced_sizes[doc_id] and doc_id not in sent_ids.keys():
                    sent_id = ".".join(line.split('\t')[9].split('.')[:-1])
                    sent_ids[doc_id] = sent_id

    # write to target
    with open(source, 'r') as f, open(target, 'w') as out:
        for line in tqdm(f):
            if line.startswith('<text id'):
                writing_mode = True  # flag for writing/skipping lines from a source
                out.write(line)
                doc_id = line.split()[1].split('=')[1][1:-1]

            elif writing_mode:
                if line.startswith('<s id'):  # check if new sentence is starting
                    sent_id = line[7:-3]
                    if sent_ids[doc_id] == sent_id:  # check if a new sentence is the same as the sentence that exceeds 10%
                        # turn off writing mode and write closing tags
                        out.write('</p>\n')
                        out.write('</text>\n')
                        writing_mode = False
                    else:
                        out.write(line)
                else:
                    out.write(line)


if __name__ == '__main__':
    # import annotator
    classla.download('sl', type='standard_jos')
    nlp = classla.Pipeline('sl',
                           processors="tokenize,pos,ner,lemma,depparse",
                           type='standard_jos',
                           pos_use_lexicon=True,
                           # use_gpu=False
                           # tokenize_batch_size=32,
                           # ner_batch_size=32,
                           # pos_batch_size=5000,
                           # lemma_batch_size=50,
                           # depparse_batch_size=5000
                           )

    # annotate
    old2new(source='data/maks/maks.conllu-v1', output='data/maks/maks.conllu-v2')

    # convert2txt
    conllu2txt('/home/azagar/myfiles/annotation/data/maks/maks.conllu-original', '/home/azagar/myfiles/annotation/data/maks/maks.txt')

    # select 10% of each element
    reduce_doc_size('/home/azagar/myfiles/annotation/data/maks/maks4list.vert/maks4list.vert',
                    '/home/azagar/myfiles/annotation/data/maks/maks4list.vert/maks4list.smaller.vert')
