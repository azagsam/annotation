import os
from conllu import parse
from tqdm import tqdm
import classla
from collections import defaultdict


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
