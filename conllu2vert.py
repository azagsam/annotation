import os

from conllu import parse
from tqdm import tqdm


def conllu2vert(source, target):
    def reorder_tokens(output_tokens, sent_id):
        reordered_output = []
        for conllu_token in output_tokens:
            tokens = conllu_token.split('\t')
            reordered = tokens[1:] + [tokens[0]]
            reordered[9] = sent_id + '.t' + reordered[9]  # improve token id
            reordered = "\t".join(reordered)
            reordered_output.append(reordered)
        return reordered_output

    def get_ner_type(token_ner):
        entities_conversion_dict = {
            'B-PER': 'per',
            'B-DERIV-PER': 'deriv-per',
            'B-LOC': 'loc',
            'B-ORG': 'org',
            'B-MISC': 'misc',
        }
        for ent_type in entities_conversion_dict.keys():
            if ent_type in token_ner:
                return entities_conversion_dict[ent_type]

    for file in tqdm(os.listdir(source)):
        file_id = file.split('.')[0]
        source_file = os.path.join(source, file_id + '.conllu')
        target_file = os.path.join(target, file_id + '.vert')

        # open files for reading and writing
        with open(source_file, 'r') as f, open(target_file, 'w') as out:
            sentences = parse(f.read())
            for sentence in sentences:
                sentence_keys = sentence.metadata.keys()

                # write new doc tag
                if 'newdoc id' in sentence_keys:
                    doc_num = sentence.metadata['newdoc id']
                    out.write(f'<text id=\"{doc_num}\">')
                    out.write('\n')

                # write paragraph tags
                if 'newpar id' in sentence_keys:
                    newpar_id = int(sentence.metadata['newpar id'].split('.')[-1])
                    par_id = sentence.metadata["newpar id"]
                    # catch first paragraph
                    if newpar_id == 1:
                        out.write(f'<p id=\"{par_id}\">')
                        out.write('\n')
                    # catch middle paragraphs
                    else:
                        out.write('</p>')
                        out.write('\n')
                        out.write(f'<p id=\"{par_id}\">')
                        out.write('\n')

                # start writing a sentence
                sent_id = sentence.metadata["sent_id"]
                out.write(f'<s id=\"{sent_id}\">')
                out.write('\n')

                # transform tokens back to original conllu
                output_tokens = [conllu_token for conllu_token in sentence.serialize().split('\n') if
                                 conllu_token and not conllu_token.startswith('#')]  # skip metadata and empty lines
                output_tokens = reorder_tokens(output_tokens, sent_id)

                # get glued and ner tokens info
                output_ner = [output_line.split('\t')[-2] for output_line in output_tokens]

                for idx, output_line in enumerate(output_tokens):

                    # check ner
                    token_ner = output_line.split('\t')[-2]
                    if idx + 1 < len(output_tokens):
                        next_token_ner = output_ner[idx + 1]
                    else:
                        next_token_ner = 'NER=O-end_of_document'

                    if not token_ner.startswith('NER=O'):

                        if token_ner.startswith('NER=B'):
                            ner_type = get_ner_type(token_ner)
                            out.write(f'<name type=\"{ner_type}\">')
                            out.write('\n')
                            out.write(output_line)
                            out.write('\n')

                            # if ner consists of only one name
                            if next_token_ner.startswith('NER=O') or next_token_ner.startswith('NER=B'):
                                out.write('</name>')
                                out.write('\n')

                            if 'SpaceAfter=No' in output_line:
                                out.write('<g/>')
                                out.write('\n')

                        if token_ner.startswith('NER=I'):
                            out.write(output_line)
                            out.write('\n')

                            # ner sometimes consists of more than two tokens, e.g., ['B', 'I', 'I'], therefore you have to check ner for the next token, if it doesnt exist name is complete
                            if not next_token_ner.startswith('NER=I'):
                                out.write('</name>')
                                out.write('\n')

                            if 'SpaceAfter=No' in output_line:
                                out.write('<g/>')
                                out.write('\n')
                    else:
                        out.write(output_line)
                        out.write('\n')
                        if 'SpaceAfter=No' in output_line:
                            out.write('<g/>')
                            out.write('\n')

                # close a sentence
                out.write('</s>')
                out.write('\n')

            # close the last paragraph and the last doc tags
            out.write('</p>')
            out.write('\n')
            out.write('</text>\n')


def vert4list(source, target, concatenated=False):
    """
    This functions transforms vert for program LIST

    Iglice iglica NOUN Sozmi Case=Nom|Gender=Fem|Number=Plur 0 modra _ NER=O 1

    v (prva črka prekopirana iz četrtega stolpca spojena z vezajem z lemo, spremenjena iz velike v malo črko):

    Iglice iglica-s NOUN Sozmi Case=Nom|Gender=Fem|Number=Plur 0 modra _ NER=O 1

    Regi pa mora nujno vsebovati naslednje atribute (točno v tem vrstnem redu):

    ATTRIBUTE word
    ATTRIBUTE lempos {
    LABEL "lemma with pos tag"
    }
    ATTRIBUTE tag_upos {
    LABEL "Universal part-of-speech tag"
    }
    ATTRIBUTE tag {
    LABEL "Language-specific part-of-speech tag."
    }

    concatenated: create one file
    """

    if concatenated:
        target_file = os.path.join(target, target.split('/')[-1])
        with open(target_file, 'w') as out:
            for file in tqdm(os.listdir(source)):
                file_id = file.split('.')[0]
                source_file = os.path.join(source, file_id + '.vert')

                with open(source_file, 'r') as inp:
                    for line in inp:
                        line_list = line.split('\t')
                        if len(line_list) == 10:
                            line_list[1] = line_list[1] + '-' + line_list[3][0].lower()
                            out.write("\t".join(line_list))
                        else:
                            out.write(line)
    else:
        for file in tqdm(os.listdir(source)):
            file_id = file.split('.')[0]
            source_file = os.path.join(source, file_id + '.vert')
            target_file = os.path.join(target, file_id + '.vert')

            with open(source_file, 'r') as inp, open(target_file, 'w') as out:
                for line in inp:
                    line_list = line.split('\t')
                    if len(line_list) == 10:
                        line_list[1] = line_list[1] + '-' + line_list[3][0].lower()
                        out.write("\t".join(line_list))
                    else:
                        out.write(line)


if __name__ == '__main__':
    conllu2vert('data/maks/maks.conllu-jos_standard-slo', 'data/maks/maks.vert')
    vert4list('data/maks/maks.vert', 'data/maks/maks4list_unconcatenated.vert', concatenated=False)

    conllu2vert('data/ucbeniki/ucbeniki.conllu-jos_standard-slo', 'data/ucbeniki/ucbeniki.vert')
    vert4list('data/ucbeniki/ucbeniki.vert', 'data/ucbeniki/ucbeniki4list_unconcatenated.vert', concatenated=False)
