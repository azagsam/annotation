import os

import json

import conllu
from conllu import parse
from tqdm import tqdm
import classla
from collections import defaultdict
import numpy as np
import re
import shutil

import tempfile


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


def reduce_doc_size(source, target, skip=None, write_last_sentence_ids_ccmaks=None):
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
                    par_id, s_id = int(sent_id.split('.')[1]),  int(sent_id.split('.')[2])
                    if par_id == 1 and s_id == 1:  # include the first sentence, even if it exceeds 10% of the text
                        continue
                    sent_ids[doc_id] = sent_id

    for doc_id in counter.keys():  # one document contains only one sentence
        if doc_id not in sent_ids.keys():
            print(doc_id)
            sent_ids[doc_id] = doc_id+'.1.2'  # something other than x.1.1

    if write_last_sentence_ids_ccmaks:
        with open(write_last_sentence_ids_ccmaks, 'w') as f:
            for doc_id, sent_id in sent_ids.items():
                f.write(f"{doc_id}\t{sent_id}\n")

    # write to target
    non_skipped_files_ids = []
    with open(source, 'r') as f, open(target, 'w') as out:
        for line in tqdm(f):
            if line.startswith('<text id'):
                writing_mode = True  # flag for writing/skipping lines from a source
                out.write(line)
                doc_id = line.split()[1].split('=')[1][1:-1]

            elif writing_mode:
                if line.startswith('<s id'):  # check if new sentence is starting
                    sent_id = line[7:-3]
                    if sent_ids[doc_id] == sent_id and doc_id not in skip:  # check if a new sentence is the same as the sentence that exceeds 10% and not in a skip list
                        # turn off writing mode for files that are not in skip and write closing tags
                        non_skipped_files_ids.append(doc_id)
                        out.write('</p>\n')
                        out.write('</text>\n')
                        writing_mode = False
                    else:
                        out.write(line)
                else:
                    out.write(line)
    print('Non-skipped files:', len(non_skipped_files_ids))


def build_ccmaks_vert():
    # paths
    ccgigafida_maks = '/home/azagar/myfiles/annotation/data/ccgigafida/ccgigafida_ccmaks4list_unconcatenated.vert'
    maks4list_unconcatenated = '/home/azagar/myfiles/annotation/data/ccmaks/maks4list_unconcatenated.vert'
    maks_header = '/home/azagar/myfiles/annotation/data/maks/maks_header.txt'

    # gather all documents
    docs = {}
    ccgigafida_maks_ids = set()
    for file in os.listdir(ccgigafida_maks):  # add gigafida docs
        full_path = os.path.join(ccgigafida_maks, file)
        with open(full_path, 'r') as f:
            lines = f.readlines()
            doc_id = file.split('.')[0]
            ccgigafida_maks_ids.add(doc_id)
            docs[doc_id] = lines

    for file in os.listdir(maks4list_unconcatenated):  # add maks docs
        doc_id = file.split('.')[0]
        if doc_id not in docs.keys():  # skip gigafida docs
            full_path = os.path.join(maks4list_unconcatenated, file)
            with open(full_path, 'r') as f:
                lines = f.readlines()
                docs[doc_id] = lines

    # get metadata
    metadata = {}
    with open(maks_header, 'r') as h:
        for line in h:
            doc_id = line.split()[1].split('=')[1][1:-1]
            metadata[doc_id] = line

    docs_with_metadata = {}
    for doc_id, lines in docs.items():
        docs_with_metadata[doc_id] = [metadata[doc_id]] + lines[1:]  # replace first line with metadata line

    # create temp file for reducing doc size
    tmp = tempfile.NamedTemporaryFile()
    sorted_docs = sorted(docs_with_metadata.keys(), key=lambda x: int(re.findall(r'\d+', x)[0]))
    for doc_id in sorted_docs:
        lines = docs_with_metadata[doc_id]
        for line in lines:
            tmp.write(line.encode('utf-8'))

    reduce_doc_size(tmp.name, '/home/azagar/myfiles/annotation/data/ccmaks/ccmaks4list.vert/ccmaks4list.vert', skip=ccgigafida_maks_ids,
                    write_last_sentence_ids_ccmaks='/home/azagar/myfiles/annotation/data/ccmaks/ccmaks4list_last_sentence_ids.txt')


def build_ccmaks_conllu():
    data = {}
    with open('/home/azagar/myfiles/annotation/data/ccmaks/ccmaks4list_last_sentence_ids.txt', 'r') as f:
        for line in f:
            doc_id, sent_id = line.strip().split('\t')
            data[doc_id] = sent_id

    gigafida_ids = [file.split('.')[0] for file in os.listdir('/home/azagar/myfiles/annotation/data/ccgigafida/ccgigafida_ccmaks4list_unconcatenated.vert')]
    ccgigafida_ccmaks = '/home/azagar/myfiles/annotation/data/ccgigafida/ccgigafida_ccmaks.conllu-jos_standard-slo'
    source = '/home/azagar/myfiles/annotation/data/ccmaks/maks.conllu-jos_standard-slo'
    target = '/home/azagar/myfiles/annotation/data/ccmaks/ccmaks.conllu'
    for file in os.listdir(source):
        source_path = os.path.join(source, file)
        target_path = os.path.join(target, file)
        doc_id = file.split('.')[0]
        if doc_id in gigafida_ids:
            ccgigafida_ccmaks_path = os.path.join(ccgigafida_ccmaks, file)
            shutil.copyfile(ccgigafida_ccmaks_path, target_path)
        else:
            with open(source_path, 'r') as f, open(target_path, 'w') as out:
                sentences = parse(f.read())
                for sent in sentences:
                    sent_id = sent.metadata['sent_id']
                    if sent_id == data[doc_id]:
                        break
                    else:
                        out.write(sent.serialize())


def find_small_docs(source_folder, target_file):
    # find small docs
    small_docs = []
    for file in tqdm(os.scandir(source_folder)):
        with open(file.path) as f:
            data = conllu.parse(f.read())
            if len(data) < 10:
                small_docs.append(data[0].metadata['newdoc id'])  # first sentence include information about document id
    sorted_docs = sorted(small_docs, key=lambda x: int(re.findall(r'\d+', x)[0]))

    # write to disk
    with open(target_file, 'w') as out:
        for file in sorted_docs:
            out.write(file)
            out.write('\n')


if __name__ == '__main__':
    # # import annotator
    # classla.download('sl', type='standard_jos')
    # nlp = classla.Pipeline('sl',
    #                        processors="tokenize,pos,ner,lemma,depparse",
    #                        type='standard_jos',
    #                        pos_use_lexicon=True,
    #                        # use_gpu=False
    #                        # tokenize_batch_size=32,
    #                        # ner_batch_size=32,
    #                        # pos_batch_size=5000,
    #                        # lemma_batch_size=50,
    #                        # depparse_batch_size=5000
    #                        )
    #
    # # annotate
    # old2new(source='data/maks/maks.conllu-v1', output='data/maks/maks.conllu-v2')
    #
    # # convert2txt
    # conllu2txt('/home/azagar/myfiles/annotation/data/maks/maks.conllu-original', '/home/azagar/myfiles/annotation/data/maks/maks.txt')
    #
    # # select 10% of each element
    # reduce_doc_size('/home/azagar/myfiles/annotation/data/maks/maks4list.vert/maks4list.vert',
    #                 '/home/azagar/myfiles/annotation/data/maks/maks4list.vert/maks4list.smaller.vert')

    # find small documets
    find_small_docs('/home/azagar/myfiles/annotation/data/maks/maks.conllu-original', '/home/azagar/myfiles/annotation/data/ccmaks/ccmaks_removed_docs.txt')

    # create ccmaks
    # build_ccmaks_vert()
    # build_ccmaks_conllu()