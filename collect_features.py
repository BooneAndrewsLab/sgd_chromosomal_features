#!/usr/bin/env python

from intermine.webservice import Service


def fetch_from_sgd() -> dict:
    """Query SGD's intermine service and return an up-to-date dict of S. Cerevisiae features (genes).
    Returned is a dictionary of "SGD_ID" -> dict of feature data. Keys in feature data are:
    sgd_id, feature_qualifier, feature_type, orf, name, aliases, chromosome, chromosomal_location, start_coordinate,
    stop_coordinate, description

    :rtype: dict
    """
    service = Service("https://yeastmine.yeastgenome.org:443/yeastmine/service")
    query = service.new_query("Gene")
    query.add_view(
        "primaryIdentifier", "featureType", "qualifier", "secondaryIdentifier",
        "symbol", "chromosomeLocation.start", "chromosomeLocation.end",
        "description", "synonyms.value"
    )
    query.add_constraint("Gene", "IN", "ALL_Verified_Uncharacterized_Dubious_ORFs", code="A")

    genes = {}

    for row in query.rows():
        sgd_id = row["primaryIdentifier"]
        orf = row["secondaryIdentifier"]

        if orf.startswith('Q'):
            chrom = 0
            orfnum = int(orf[1:])
        else:
            chrom = ord(orf[1]) - 64
            orfnum = int(orf[3:6])
            if orf[2] == 'L':
                orfnum = -orfnum

        if sgd_id not in genes:
            genes[sgd_id] = {
                'sgd_id': row["primaryIdentifier"],
                'feature_qualifier': row["qualifier"],
                'feature_type': row['featureType'],
                'orf': orf,
                'name': row["symbol"],
                'aliases': [],
                'chromosome': chrom,
                'chromosomal_location': orfnum,
                'start_coordinate': str(row["chromosomeLocation.start"]),
                'stop_coordinate': str(row["chromosomeLocation.end"]),
                'description': row["description"],
            }

        if row["synonyms.value"] not in (orf, row["symbol"]):
            genes[sgd_id]['aliases'].append(row["synonyms.value"])

    return genes


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Fetch Saccharomyces Cerevisiae\'s features')
    parser.add_argument('-o', '--output', dest='output', type=argparse.FileType('w'), default=sys.stdout)

    args = parser.parse_args()

    features = fetch_from_sgd()

    for sgdid, gene in features.items():
        output_row = [
            sgdid,
            gene['feature_type'],
            gene['feature_qualifier'],
            gene['orf'],
            gene['name'] or '',
            str(gene['chromosome']),
            gene['start_coordinate'],
            gene['stop_coordinate'],
            gene['description'],
            '|'.join(gene['aliases'])
        ]

        args.output.write('\t'.join(output_row) + '\n')
