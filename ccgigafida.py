import os
import re
import xml.etree.ElementTree as ET
import classla
from tqdm import tqdm
from bs4 import BeautifulSoup
import pandas as pd
import shutil


def annotate(source, output):
    df = pd.read_csv('data/maks/maks-metadata.csv', sep=';')

    files = [(m, g + '.txt') for m, g in zip(df['maks_id'], df['gigafida_id'])]

    for t in tqdm(files):
        maks_id, file = t
        print(file)
        doc_id = 'maks' + str(maks_id)

        # output_ids = [os.path.splitext(f)[0] for f in os.listdir(output)]
        # if doc_id in output_ids:
        #     continue

        with open(os.path.join(source, file), 'r') as f:
            text = f.read()

            # annotate
            try:
                doc = nlp(text)

                # prepare for output
                classla_out = doc.to_conll()
                ccgigafida_out = ""
                for line in classla_out.splitlines():
                    if line.startswith('# newpar id') or line.startswith('# sent_id'):
                        key, value = line.split(' = ')
                        new_line = f"{key} = {doc_id}.{value}"
                        ccgigafida_out += new_line + "\n"
                    else:
                        ccgigafida_out += line + '\n'
                ccgigafida_out = f"# newdoc id = {doc_id}\n" + ccgigafida_out

                # write
                out_path = os.path.join(output, doc_id + '.conllu')
                with open(out_path, 'w', encoding='utf-8') as out:
                    out.write(ccgigafida_out)

            except RuntimeError as e:
                if str(e).startswith('CUDA out of memory.'):
                    with open('failed-ccgigafida.txt', 'a') as f:
                        f.write(doc_id)
                        f.write('\n')
                else:
                    print('Other type of error')



if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = '1'

    # import annotator
    classla.download('sl', type='standard_jos')
    nlp = classla.Pipeline('sl',
                           processors="tokenize,pos,ner,lemma,depparse",
                           type='standard_jos',
                           pos_use_lexicon=True,
                           # use_gpu=False,
                           # tokenize_batch_size=32,
                           # ner_batch_size=32,
                           # pos_batch_size=5000,
                           # lemma_batch_size=50,
                           # depparse_batch_size=5000
                           )

    annotate('/home/azagar/myfiles/annotation/data/ccgigafida/ccGigafidaV1_0-text', '/home/azagar/myfiles/annotation/data/ccgigafida/ccgigafida_ccmaks.conllu/')
