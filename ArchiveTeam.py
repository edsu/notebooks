
# coding: utf-8

# # ArchiveTeam Growth

# This notebook lets you calculate the growth of the data deposited at the Internet Archive by ArchiveeTeam. It just uses the Internet Archive API to look through the metadata for all their items.
# 
# ## Install
# 
# If you are reading this you may have Jupyter already set up, but just in case you don't you'll want to install Python 3 and:
# 
#     % pip install pipenv
#     % git clone https://github.com/edsu/growth
#     % cd growth
#     % pipenv install
#     
# And now you'll need to save your Internet Archive account login details. If you don't have an account go over to archive.org and create one, and then:
# 
#     % ia configure
#     
# ## Internet Archive Metadata
# 
# Now we're ready to load and use the [internetarchive](https://github.com/jjjake/internetarchive) Python extension:
#     

# In[ ]:


import internetarchive as ia


# Internet Archive organizes their stuff according to *collections*, which can contain one or many *items*. Each item then can contain one or many files. Collections and items have identifiers that uniquely identify them. For example if you know the the item identifier `ARCHIVEIT-2410-DAILY-JOB227586-20160728-00000` you can go get it and print its metadata:

# In[ ]:


from pprint import pprint

item = ia.get_item('archiveteam_tumblr20181221175524')
pprint(item.metadata)


# Notice that the item identifier `archiveteam_tumblr20181221175524` contains a date/time? We're going to take a bit of a leap here and assume that the date contained in there is the date that the WARC data was collected from SavePageNow. This might in fact not be the case, unless we learn more from Internet Archive about the provenance of this data.
# 
# There's actually much more detailed metadata available for the files in the item. Here's how many files are in the item:

# In[ ]:


print(len(item.item_metadata['files']))


# We can see what metadata is available for the first file:

# In[ ]:


pprint(item.item_metadata['files'][0])


# See the *size* property? That's the size in bytes of the file.
# 
# ## Fetch the Data
# 
# So now we know enough to write a function that can return the date and the size of the warc files in an item given its identifier.

# In[ ]:


import re

def item_summary(item_id):
    item = ia.get_item(item_id)

    size = 0
    for file in item.item_metadata['files']:
        if 'size' in file:
            size += int(file['size'])
            
    m = re.match('(^\d\d\d\d-\d\d-\d\d)', item.item_metadata['metadata']['addeddate'])
    date = m.group(1)
    
    return date, size


# Let's give a try:

# In[ ]:


print(item_summary('archiveteam_tumblr20181221175524'))


# The internetarchive Python library doesn't offer an abstraction for collections. But it does provide a way to search for a collection and iterate through the items that it contains. If you now the name of your collection you can iterate through it pretty easily. So lets see how many items are contained in the collection:

# In[ ]:


num_items = len(ia.search_items('collection:archiveteam'))
print(num_items)


# That's quite a few. If it takes a second to get the metadata for each item we are going to need to wait a while:

# In[ ]:


print(num_items / 60 / 60.0, 'hours')


# Ok, so let's go through each item, get the size and day for the item, and store them in a dictionary. Since there may be more than one item in a day it's important to add to the existing value for a date instead of simply storing it.

# In[ ]:


import os
import re
import json

sizes = {}

if not os.path.isfile('ArchiveTeam.csv'):

    for result in ia.search_items('collection:archiveteam'):
        date, size = item_summary(result['identifier'])
        sizes[date] = sizes.get(date, 0) + size
        print(result['identifier'], date, size, sizes[date])


# Now we can write out the *sizes* dictionary to a CSV file, where every row is a date. This way we won't need to fetch it every time we run this notebook.

# In[ ]:


if sizes:

    import csv

    dates = sorted(sizes.keys())

    with open('ArchiveTeam.csv', 'w') as output:
        writer = csv.writer(output)
        writer.writerow(['date', 'size'])
        for date in dates:
            writer.writerow([date, sizes[date]])

