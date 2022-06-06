import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

from bs4 import BeautifulSoup
from tqdm import tqdm


def parse_ucbeniki_metadata(xml_file):
    # parse xml
    tree = ET.parse(xml_file, )

    # define namespace
    ns = '{http://www.tei-c.org/ns/1.0}'
    works = f'{ns}div'
    bibl = f'{ns}bibl'

    body = list(tree.iter('{http://www.tei-c.org/ns/1.0}body'))[0]
    with open('data/ucbeniki/ucbeniki4list.vert/ucbeniki_header.txt', 'w') as out:
        for work in body.iter(works):
            work_id = work.attrib['{http://www.w3.org/XML/1998/namespace}id']

            d = defaultdict(list)
            for b in work.iter(bibl):
                for e in b.iter():
                    d[e.tag.replace(ns, '')].append(e.text)
            print(work_id, d)

            # <text id="maks208" title="Lepota" year="2018" publisher="Salomon, d. o. o." channel="publicistika" keyword="zdravje in telesna nega|lepota|akupunktura|obraz|pomlajevanje">
            terms = "|".join(d["term"])
            header = f'<text id="{work_id}" title="{d["title"][0]}" publisher="{d["publisher"][0]}" year="{d["date"][0]}" note="{d["note"][0]}" term="{terms}">\n'
            out.write(header)


def parse_maks_metadata(maks_root):
    for m in tqdm(os.listdir(maks_root)):
        if 'div' in m:
            xml_file = os.path.join(maks_root, m)
            if m != 'maks1367.div.xml':
                continue

            with open(xml_file, 'r') as fp, open('data/maks/maks_header.txt', 'a') as out:
                soup = BeautifulSoup(fp, 'xml')
                bibl_element = soup.find_all('bibl')
                assert len(bibl_element) == 1

                bibl_element = bibl_element[0]
                d = defaultdict(list)
                work_id = bibl_element.attrs['n']
                for e in bibl_element.find_all():
                    d[e.name].append(e.text)
                # print(work_id, d)

                terms = "|".join(d["term"])
                if 'pubPlace' in d.keys():
                    header = f'<text id="{work_id}" title="{d["title"][0]}" publisher="{d["publisher"][0]}" pubPlace="{d["pubPlace"][0]}" date="{d["date"][0]}" term="{terms}">\n'
                else:
                    header = f'<text id="{work_id}" title="{d["title"][0]}" publisher="{d["publisher"][0]}" date="{d["date"][0]}" term="{terms}">\n'
                out.write(header)


def replace_vert_head(source, target, header):
    source_files = os.listdir(source)
    source_files.sort(key=lambda x: int(re.findall('\d+', x)[0]))

    d = {}
    with open(header, 'r') as h:
        for line in h:
            doc_id = line.split()[1].split('=')[1][1:-1]
            d[doc_id] = line

    with open(target, 'w') as out:
        for file in tqdm(source_files):
            doc_id = file[:-5]
            file_path = os.path.join(source, file)
            with open(file_path, 'r') as f:
                for idx, line in enumerate(f):
                    if idx == 0:
                        out.write(d[doc_id])
                    else:
                        out.write(line)


if __name__ == '__main__':
    # xml_file = 'data/ucbeniki/ucbeniki-sl.xml'
    # parse_ucbeniki_metadata(xml_file)

    # replace_vert_head('/home/azagar/myfiles/annotation/data/ucbeniki/ucbeniki4list_unconcatenated.vert',
    #                       '/home/azagar/myfiles/annotation/data/ucbeniki/ucbeniki4list.vert/ucbeniki4list.vert',
    #                       '/home/azagar/myfiles/annotation/data/ucbeniki/ucbeniki_header.txt')

    # maks_root = 'data/maks/maks.tei'
    # parse_maks_metadata(maks_root)

    replace_vert_head('/home/azagar/myfiles/annotation/data/maks/maks4list_unconcatenated.vert',
                      '/home/azagar/myfiles/annotation/data/maks/maks4list.vert/maks4list.vert',
                      '/home/azagar/myfiles/annotation/data/maks/maks_header.txt')
