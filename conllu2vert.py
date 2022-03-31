from conllu import parse

file = 'data/maks/maks.conllu-jos_standard-slo/maks1.conllu'
with open(file, 'r') as f, open('maks1.vert', 'w') as out:
    sentences = parse(f.read())
    for sentence in sentences:
        sentence_keys = sentence.metadata.keys()

        # write new doc tag
        if 'newdoc id' in sentence_keys:
            doc_num = sentence.metadata['newdoc id']
            out.write(f'<doc id=\"{doc_num}\">')
            out.write('\n')

        # write paragraph tags
        if 'newpar id' in sentence_keys:
            # check first
            newpar_id = int(sentence.metadata['newpar id'].split('.')[-1])
            if newpar_id == 1:
                out.write('<p>')
                out.write('\n')
            # check middle
            else:
                out.write('</p>')
                out.write('\n')
                out.write('<p>')
                out.write('\n')

        # serialize
        output_tokens = [conllu_token for conllu_token in sentence.serialize().split('\n') if not conllu_token.startswith('#')]
        output_tokens = ['\t'.join(conllu_token.split('\t')[1:]) for conllu_token in output_tokens]

        # start writing tokens in a sentence
        out.write('<s>')
        out.write('\n')

        # extract text
        text = sentence.metadata['text']

        # get glued tokens info
        tokens = [token['form'] for token in sentence]
        for idx, token in enumerate(tokens):
            out.write(output_tokens[idx])
            out.write('\n')
            text = text[len(token):]  # delete raw token
            # check if token is glued or not
            if text:
                if text[0] != ' ':
                    out.write('<g/>')
                    out.write('\n')
                else:
                    text = text.lstrip()

        # Finish writing tokens in a sentence
        out.write('</s>')
        out.write('\n')

    # close the last paragraph and the last doc tags
    out.write('</p>')
    out.write('\n')
    out.write('</doc>')