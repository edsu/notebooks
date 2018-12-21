
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

# In[4]:


import internetarchive as ia


# Internet Archive organizes their stuff according to *collections*, which can contain one or many *items*. Each item then can contain one or many files. Collections and items have identifiers that uniquely identify them. For example if you know the the item identifier `ARCHIVEIT-2410-DAILY-JOB227586-20160728-00000` you can go get it and print its metadata:

# In[5]:


from pprint import pprint

item = ia.get_item('archiveteam_tumblr20181221175524')
pprint(item.metadata)


# Notice that the item identifier `archiveteam_tumblr20181221175524` contains a date/time? We're going to take a bit of a leap here and assume that the date contained in there is the date that the WARC data was collected from SavePageNow. This might in fact not be the case, unless we learn more from Internet Archive about the provenance of this data.
# 
# There's actually much more detailed metadata available for the files in the item. Here's how many files are in the item:

# In[6]:


print(len(item.item_metadata['files']))


# We can see what metadata is available for the first file:

# In[7]:


pprint(item.item_metadata['files'][0])


# See the *size* property? That's the size in bytes of the file.
# 
# ## Fetch the Data
# 
# So now we know enough to write a function that can return the date and the size of the warc files in an item given its identifier.

# In[24]:


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

# In[25]:


print(item_summary('archiveteam_tumblr20181221175524'))


# The internetarchive Python library doesn't offer an abstraction for collections. But it does provide a way to search for a collection and iterate through the items that it contains. If you now the name of your collection you can iterate through it pretty easily. So lets see how many items are contained in the collection:

# In[26]:


num_items = len(ia.search_items('collection:archiveteam'))
print(num_items)


# That's quite a few. If it takes a second to get the metadata for each item we are going to need to wait a while:

# In[27]:


print(num_items / 60 / 60.0, 'hours')


# Ok, so let's go through each item, get the size and day for the item, and store them in a dictionary. Since there may be more than one item in a day it's important to add to the existing value for a date instead of simply storing it.

# In[33]:


import os
import re
import json

sizes = {}

if not os.path.isfile('Growth.csv'):

    for result in ia.search_items('collection:archiveteam'):
        date, size = item_summary(result['identifier'])
        sizes[date] = sizes.get(date, 0) + size
        print(result['identifier'], date, size, sizes[date])


# Now we can write out the *sizes* dictionary to a CSV file, where every row is a date. This way we won't need to fetch it every time we run this notebook.

# In[34]:


if sizes:

    import csv

    dates = sorted(sizes.keys())

    with open('Growth.csv', 'w') as output:
        writer = csv.writer(output)
        writer.writerow(['date', 'size'])
        for date in dates:
            writer.writerow([date, sizes[date]])

#
## ## Analyze the Data
## 
## So now we have our CSV of data we can analyze it a bit with [pandas](https://pandas.pydata.org/) and maybe generate a useful graph. First we'll import pandas and load in the data as a pandas DataFrame.
## 
## *Aside: I'm still learning pandas, and this is not meant to be a tutorial. If you want to learn more about all the amazing stuff you can do with it you'll want to spend some time in their excellent [tutorial](https://pandas.pydata.org/pandas-docs/stable/dsintro.html). If you work with R at all it should look pretty familiar. If not, treat this as just dipping your toe in to test the water. That's what I'm doing. If you do know pandas and notice a better way of doing any of this please let me know!*
#
## In[35]:
#
#
#import pandas as pd
#
#sizes = pd.read_csv('Growth.csv', index_col=0, parse_dates=True)
#sizes.head()
#
#
## It looks like the liveweb data started saving back in 2011. So now we've got a DataFrame that is indexed by the day, with one Series *size* that contains the bytes. I don't know about you, but I find it difficult to think of size in terms of bytes. So let's use pandas to calcuate a gigabyte column for us using the bytes:
#
## In[36]:
#
#
#sizes = sizes.assign(gb=lambda x: x / 1024 ** 3)
#sizes.head()
#
#
## Now we can tell pandas to calcuate some statistics on our data:
#
## In[37]:
#
#
#sizes.describe()
#
#
## ## Visualize the Data
## 
## Since we have thousands of days, it might be useful to see the stats by month rather than by day. That's not too hard to do since our dataframe as a date index and pandas support for [timeseries](https://pandas.pydata.org/pandas-docs/stable/timeseries.html#timeseries) data allows us to resample the dataframe on a monthly basis:
#
## In[38]:
#
#
#sizes_by_month = sizes.resample('M').sum()
#sizes_by_month.head()
#
#
## In[39]:
#
#
#get_ipython().run_line_magic('matplotlib', 'inline')
#
#sizes_by_month['gb'].plot()
#
#
## Kinda cool right!? The dip at the end is the result of me running the data collection at the beginning of November. So let's remove that:
#
## In[25]:
#
#
#import datetime
#
#sizes_without_nov = sizes_by_month['gb'].drop(datetime.date(2018, 11, 30))
#
#plot = sizes_without_nov
#.plot(figsize=(12, 5))
#plot.set_xlabel('Year')
#plot.set_ylabel('Gigabytes per Month')
#plot.set_title('Save-Page-Now Ingest Rate')
#
#
## ## Estimating Storage for Samples
## 
## As part of our research project we are looking to explore and characterize the data that is being archived by SPN. Part of this will involve looking at what URLs and domains are being collected, the HTTP headers that the client is sending (which preserving the anonymity of the client), and also perhaps some content analysis. Downloading 296 TB isn't probably going to be feasible, so we are planning to sample the data in two ways: interval and event based sampling. In order to prepare our own analysis environment we need to calculate how much storage we're going to need.
## 
## ### Sampling by Interval
## 
## For the systematic sampling we are going to download a day of WARC data at routine intevals. Starting at the beginning of the SPN data up to the present day. We can use our data to figure out the start end end of the time period, and then use pandas to calcuate the dates we want to look at.
#
## In[20]:
#
#
#start_date = min(sizes.index)
#end_date = max(sizes.index)
#annual = pd.date_range(start_date, end_date, freq='A')
#print(annual)
#
#
## Then we can use pandas to tell us the data sizes on those days as well as the total.
#
## In[21]:
#
#
#annual_sizes = sizes['gb'].filter(annual)
#print(annual_sizes)
#print()
#print("Annual: %0.2f TB" % (sum(annual_sizes)/1024))
#
#
## We're not actually sure exactly how much storage space we'll have available to us so it could be useful to have some other ranges and their totals handy:
#
## In[22]:
#
#
#print("Biannual: %0.2f TB" % (sum(sizes['gb'].filter(pd.date_range(start_date, end_date, freq='6M'))) / 1024))
#print("Monthly: %0.2f TB" % (sum(sizes['gb'].filter(pd.date_range(start_date, end_date, freq='1M'))) / 1024))
#print("Biweekly: %0.2f TB" % (sum(sizes['gb'].filter(pd.date_range(start_date, end_date, freq='2W'))) / 1024))
#print("Weekly: %0.2f TB" % (sum(sizes['gb'].filter(pd.date_range(start_date, end_date, freq='W'))) / 1024))
#
#
## ### Sampling by Event
## 
## We also want to zoom in on particular event time periods to see if behavior around them changes significantly. Here is a short list we have for events:
## 
## * **Ferguson Protests** - 2014-08-09 - 2014-08-16
## * **Brexit Vote** - 2016-06-16 - 2016-06-24
## * **DataRescue** - 2018-01-15 - 2018-01-30
#
## In[23]:
#
#
#from datetime import date
#
#ferguson = pd.date_range(date(2014, 8, 9), date(2014, 8, 16))
#print('Ferguson %0.2f TB' % (sum(sizes['gb'].filter(ferguson)) / 1024))
#
#brexit = pd.date_range(date(2016, 6, 16), date(2016, 6, 24))
#print('Brexit %0.2f TB' % (sum(sizes['gb'].filter(brexit)) / 1024))
#
#datarescue = pd.date_range(date(2018, 1, 15), date(2018, 1, 30))
#print('DataRescue %0.2f TB' % (sum(sizes['gb'].filter(datarescue)) / 1024))
#
#
## ### Total Storage
## 
## This is accidentally kind of interesting because the DataRescue event does seem to be kind of anomlaous which you can see in the line graph above. So it looks like maximum we'd need at most **50 TB** of storage if we went with the weekly samply rate and the three events above. I suspect we'll want to have some processing space for derivative data, so maybe padding out to **75 TB** is a good idea? This will also let us decide on new events that we are interested in.
#
## In[24]:
#
#
#.3 + .94 + 6.1 + 38.8 
#
