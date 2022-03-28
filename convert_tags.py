from conversion_utils.jos_msds_and_properties import Converter, Msd, Properties

# JOS-SYN
slo2eng= {
    "modra": "Root",
    "del": "PPart",
    "dol": "Atr",
    "ena": "Sb",
    "dve": "Obj",
    "tri": "AdvM",
    "štiri": "AdvO",
    "prir": "Coord",
    "vez": "Conj",
    "skup": "MWU",
}

eng2slo = {value: key for key, value in slo2eng.items()}

sample = '/home/azagar/myfiles/annotation/data/maks/maks.conllu-jos_standard-eng/maks1.conllu'
with open(sample, 'r', encoding="utf-8") as f, open('maks1-slo.conllu', 'w') as out:
    for line in f:
        line = line.split('\t')
        if len(line) == 10:

            # JOS-SYN
            line[7] = eng2slo[line[7]]

            # JOS-MSD
            converter = Converter()
            msd_eng = Msd(line[4], 'en')
            msd_slo = converter.translate_msd(msd_eng, 'sl', lemma=line[2])
            msd_slo = msd_slo.code
            line[4] = msd_slo

        # join line
        line = "\t".join(line)
        out.write(line)

