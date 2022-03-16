import os
import xml.etree.ElementTree as ET
import classla
from tqdm import tqdm


def convert2txt():
    # import data
    xml_file = 'data/ucbeniki/ucbeniki-sl.xml'
    tree = ET.parse(xml_file)

    # define namespace
    ns = '{http://www.tei-c.org/ns/1.0}'
    # words = f'{ns}w'
    # separators = f'{ns}s'
    sentences = f'{ns}s'
    paragraphs = f'{ns}p'
    works = f'{ns}div'

    body = list(tree.iter('{http://www.tei-c.org/ns/1.0}body'))[0]
    for work in body.iter(works):
        work_title = work.attrib['{http://www.w3.org/XML/1998/namespace}id']
        print(work_title)
        with open(f'data/ucbeniki/ucbeniki.txt/{work_title}.txt', 'w') as out:
            for p in work.iter(paragraphs):
                for s in p.iter(sentences):
                    try:
                        sentence = ''.join([t.text for t in s.iter()]).strip()
                    except TypeError:  # sometimes there is no text, add empty sentence
                        sentence = ''
                    out.write(sentence)
                    out.write(' ')
                out.write('\n')


def annotate(source, output):
    for file in tqdm(os.listdir(source)):
        print(file)
        doc_id = os.path.splitext(file)[0]

        output_ids = [os.path.splitext(f)[0] for f in os.listdir(output)]
        if doc_id in output_ids:
            continue

        with open(os.path.join(source, file), 'r') as f:
            text = f.read()

            # annotate
            try:
                doc = nlp(text)

                # prepare for output
                classla_out = doc.to_conll()
                textbooks_out = ""
                for line in classla_out.splitlines():
                    if line.startswith('# newpar id') or line.startswith('# sent_id'):
                        key, value = line.split(' = ')
                        new_line = f"{key} = {doc_id}.{value}"
                        textbooks_out += new_line + "\n"
                    else:
                        textbooks_out += line + '\n'
                textbooks_out = f"# newdoc id = {doc_id}\n" + textbooks_out

                # write
                out_path = os.path.join(output, doc_id + '.conllu')
                with open(out_path, 'w', encoding='utf-8') as out:
                    out.write(textbooks_out)

            except RuntimeError as e:
                if str(e).startswith('CUDA out of memory.'):
                    with open('failed-ucbeniki.txt', 'a') as f:
                        f.write(doc_id)
                        f.write('\n')
                else:
                    print('Other type of error')


if __name__ == '__main__':
    # convert2txt()

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

    annotate('data/ucbeniki/ucbeniki.txt/', 'data/ucbeniki/ucbeniki.conllu/')
