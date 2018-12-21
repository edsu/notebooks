#!/usr/bin/env python

# extracted from ArchiveTeam.ipynb to run for a long time outside of jupyter

import re
import os
import re
import csv
import json
import internetarchive as ia

def item_summary(item_id):
    item = ia.get_item(item_id)
    size = 0
    for file in item.item_metadata['files']:
        if 'size' in file:
            size += int(file['size'])
    m = re.match('(^\d\d\d\d-\d\d-\d\d)', item.item_metadata['metadata']['addeddate'])
    date = m.group(1)
    return date, size

sizes = {}
count = 0
for result in ia.search_items('collection:archiveteam'):
    count += 1
    date, size = item_summary(result['identifier'])
    sizes[date] = sizes.get(date, 0) + size
    print(count, result['identifier'], date, size, sizes[date])

dates = sorted(sizes.keys())
with open('ArchiveTeam.csv', 'w') as output:
    writer = csv.writer(output)
    writer.writerow(['date', 'size'])
    for date in dates:
        writer.writerow([date, sizes[date]])
