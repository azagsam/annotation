import os
from tqdm import tqdm

from conversion_utils.jos_msds_and_properties import Converter, Msd, Properties


def convert_tags(source, target):
    for file in tqdm(os.listdir(source)):
        source_path = os.path.join(source, file)
        target_path = os.path.join(target, file)
        with open(source_path, 'r', encoding="utf-8") as f, open(target_path, 'w') as out:
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


def validate_tag_conversion(source, target):
    # count number of lines in source and target
    for file in tqdm(os.listdir(source)):
        # check if file exists
        if file not in os.listdir(target):
            print(f"\n{file} is missing in the target folder!")
            continue
        # check if files have identical number of lines
        source_path = os.path.join(source, file)
        target_path = os.path.join(target, file)
        with open(source_path, 'r') as src, open(target_path, 'r') as tgt:
            src_lines = len(src.readlines())
            tgt_lines = len(tgt.readlines())
            if src_lines != tgt_lines:
                print(f"\n{target_path} does not contain the same number of lines as source file")


if __name__ == '__main__':
    # JOS-SYN
    slo2eng = {
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

    source = '/home/azagar/myfiles/annotation/data/maks/maks.conllu-jos_standard-eng'
    target = '/home/azagar/myfiles/annotation/data/maks/maks.conllu-jos_standard-slo'
    print("Converting eng annotated corpus to slo annotated ... ")
    print(f"From {source} to {target}")
    convert_tags(source, target)
    validate_tag_conversion(source, target)