from conllu import parse


def reorder_tokens(output_tokens):
    reordered_output = []
    for conllu_token in output_tokens:
        tokens = conllu_token.split('\t')
        reordered = tokens[1:] + [tokens[0]]
        reordered = "\t".join(reordered)
        reordered_output.append(reordered)
    return reordered_output

n = 208
file = f'data/maks/maks.conllu-jos_standard-slo/maks{n}.conllu'
with open(file, 'r') as f, open(f'maks{n}-v2.vert', 'w') as out:
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
            # catch first paragraph
            if newpar_id == 1:
                out.write('<p>')
                out.write('\n')
            # catch middle paragraphs
            else:
                out.write('</p>')
                out.write('\n')
                out.write('<p>')
                out.write('\n')

        # transform tokens back to original conllu
        output_tokens = [conllu_token for conllu_token in sentence.serialize().split('\n') if conllu_token and not conllu_token.startswith('#')]  # skip metadata and empty lines
        output_tokens = reorder_tokens(output_tokens)

        # start writing a sentence
        out.write('<s>')
        out.write('\n')

        # extract text
        text = sentence.metadata['text']

        # get glued and ner tokens info
        for output_line in output_tokens:
            # check ner
            token_ner = output_line.split('\t')[-2].split('=')[1]  # works with spaceafter tags as well
            if 'O' not in token_ner:
                if 'B' in token_ner:
                    token_ner = token_ner.lower().split('-')[1]
                    out.write(f'<name type=\"{token_ner}\">')
                    out.write('\n')
                    out.write(output_line)
                    out.write('\n')
                    if 'SpaceAfter=No' in output_line:
                        out.write('<g/>')
                        out.write('\n')
                if 'I' in token_ner:
                    token_ner = token_ner.lower().split('-')[1]
                    out.write(output_line)
                    out.write('\n')
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
    out.write('</text>')