"""
Extracting AFDs and sorting by time
"""


import re
import requests
stns =['GRR','LAN','MKG']
from datetime import datetime
import os
from bs4 import BeautifulSoup

# https://mesonet.agron.iastate.edu/wx/afos/old.phtml

#url = "https://mesowest.utah.edu/cgi-bin/droman/meso_table_mesodyn.cgi?stn=MC093&unit=0&time=LOCAL&year1=&month1=&day1=0&hour1=00&hours=24&past=0&order=1"
#url = "https://kamala.cod.edu/mi/latest.fxus63.KGRR.html"
#url = "https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=1&glossary=0"

class TAF:


    def __init__(self, station, download=True, plot=True):
        self.station = station   # single station
        self.download = download
        self.plot = plot
        self.now = datetime.utcnow()
        self.get_taf()
        self.parse_taf()



    def get_taf(self):
        not_yet = True
        for ver in range(1,20):
            if not_yet:
                url = "https://forecast.weather.gov/product.php?site=GRR&issuedby={}&product=TAF&format=ci&version={}&glossary=0".format(self.station,ver)
                page = requests.get(url, timeout=2)
                soup = BeautifulSoup(page.content, 'html.parser')
                try:
                    nws = soup.pre
                    self.nwsStr = nws.string
                    #print(self.nwsStr)
                    if 'TAF AMD' not in self.nwsStr:
                        self.clip_taf()
                    not_yet = False
                except:
                    pass



    def clip_taf(self):
        tmp2 = []
        issue_dt = re.compile('[0-9]{6}Z')
        m = issue_dt.search(self.nwsStr)
        if m is not None:
            self.issued = m[0]
            tmp = self.nwsStr.split('\n')
            for t in range(0,len(tmp)):
                if len(tmp[t]) > 6 and ('FT' not in tmp[t]):
                    tmp2.append(tmp[t])
    
            self.txt = '\n'.join(tmp2)
        else:
            print('could not clip!')
        return
    
    def parse_taf(self):
        for line in self.txt.splitlines():
            for p in line.split():
                print(p)
        return

                
    # uniqueList = []
    
    # separator = '  -------------  '
    
    # fout = 'tafs_{}.txt'.format(self.station)
    # fpath = os.path.join("/data/scripts",fout)
    # f = open(fpath,"w")
    
    # for i in range(0,len(times)):
    #     issue_time = times[i][0]
    #     text = times[i][1]
        
    #     if issue_time not in uniqueList:
    #         head = separator  + "\n"
    #         text = head + text
    #         print(text)
    #         f.write(text)
    #         uniqueList.append(issue_time)
    #         #finalList.append(sample)
            
    # f.close()

test = TAF('GRR')