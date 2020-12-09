"""
Extracting AFDs and sorting by time
"""


import re
import requests
stns =['GRR','LAN','MKG']
from datetime import datetime,timedelta
#import os
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# https://mesonet.agron.iastate.edu/wx/afos/old.phtml

#url = "https://mesowest.utah.edu/cgi-bin/droman/meso_table_mesodyn.cgi?stn=MC093&unit=0&time=LOCAL&year1=&month1=&day1=0&hour1=00&hours=24&past=0&order=1"
#url = "https://kamala.cod.edu/mi/latest.fxus63.KGRR.html"
#url = "https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=1&glossary=0"

class TAF:

    def __init__(self, station, download=True, plot=True):
        self.station = station   # single station
        self.download = download
        self.plot = plot



        self.columns = ['time', 'WDR', 'WSP','GST','VIS','FEW','SCT','BKN','OVC','VV']
        #self.df = pd.DataFrame(index=self.idx,columns=self.columns)
        self.taf_dict = {}

        self.get_taf()
        self.clip_taf()
        self.fh_zero()
        
        self.parse_taf()
        self.finalize()

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
                        return
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

    def fh_zero(self):
        self.now = datetime.utcnow()
        dh = re.compile('(?<=\s)\d{5,}(?=Z\s)')
        mdh = dh.search(self.txt)
        if mdh is not None:
            dy = int(mdh[0][0:2])
            hr = int(mdh[0][2:4])
            self.issue_dt = self.now.replace(day=dy, hour=hr, minute=0, second=0, microsecond=0)
            self.fhzero = self.issue_dt + timedelta(hours=1)
            self.idx = pd.date_range(self.fhzero, periods=80, freq='15Min')
        else:
            print('can not find init time!')
        
        return
        
    def get_time(self):
        fm = re.compile('(?<=FM)\S{3,}(?=\s)')
        mfm = fm.search(self.line)
        if mfm is not None:
            d = int(mfm[0][0:2])
            h = int(mfm[0][2:4])
            m = int(mfm[0][4:6])
            vt = self.fhzero.replace(day=d, hour=h, minute=m)
        else:
            vt = self.fhzero
        return vt

    def get_vis(self):
        self.vv = re.compile('(?<=\s)\d\s.{3}(?=SM)')   # '1 1/2SM
        self.sm = re.compile('(?<=\s)\d(?=SM)')         # '3SM'

        m = self.vv.search(str(self.line))
        if m is not None:
            v_el = m[0].split()
            v1 = int(v_el[0])
            self.frac = v_el[1]
            v2 = self.fraction()
            vis = v1 + v2
        elif 'P6SM' in self.line:
            vis = 7            
        else:
          ss = self.sm.search(str(self.line))
          vis = int(ss[0])

        def fraction(self):
            n = self.frac.split('/')
            return int(n[0])/int(n[1])
        
        return vis
            
    
    def get_layers(self):
        self.fewm = re.compile('(?<=FEW)\d{3}')   # '1 1/2SM
        mf = self.fewm.search(self.line)
        self.sctm = re.compile('(?<=SCT)\d{3}')   # '1 1/2SM
        ms = self.sctm.search(self.line)
        self.bknm = re.compile('(?<=BKN)\d{3}')   # '1 1/2SM    
        mb = self.bknm.search(self.line)                
        self.ovcm = re.compile('(?<=OVC)\d{3}')   # '1 1/2SM    
        ob = self.ovcm.search(self.line) 
        self.vvm = re.compile('(?<=VV)\d{3}')   # '1 1/2SM
        mvv = self.vvm.search(self.line)    
        
        if mf is not None:
            few = int(mf[0])
        else:
            few = 0
            
        if ms is not None:
            sct = int(ms[0])
        else:
            sct = 0
            
        if mb is not None:
            bkn = int(mb[0])
        else:
            bkn = 0
            
        if ob is not None:
            ovc = int(ob[0])
        else:
            ovc = 0
            
        if mvv is not None:
            vv = int(mvv[0])
        else:
            vv = 0
        
        return few,sct,bkn,ovc,vv

    def get_wind(self):
        windsearch = re.compile('(?<=\s)\S{3,}(?=KT)')   # _25020G30_KT  _25015_KT
        wm = windsearch.search(self.line)
        if wm is not None:
            wind = wm[0]
            wdir = int(wind[0:3])
        if 'G' in wind:
            wind_split = wind.split['G']
            wsp = int(wind_split[0])
            g = int(wind_split[1])
        else:
            g = 0
            wsp = int(wind[-2:])
        return wdir, wsp, g

    def parse_taf(self):
        self.taf_arr = []
        for self.line in self.txt.splitlines():
            vt = self.get_time()
            wdir, ws, g = self.get_wind()
            vis = self.get_vis()
            few, sct, bkn, ovc, vv = self.get_layers()
            arr = [vt,wdir,ws,g,vis,few,sct,bkn,ovc,vv]
            self.taf_arr.append(arr)

        return 



    def finalize(self):
        self.df = pd.DataFrame(self.taf_arr, columns=self.columns)
        self.df.set_index('time', inplace=True)
        sns.set(rc={'figure.figsize':(11, 4)})
        for p in ('BKN','OVC','VIS'):

            ts = pd.Series(self.df[p])
            self.full = ts.reindex(index=self.idx,method='ffill')
        #s = self.df['wspd']
            self.full.plot(linewidth=0.5)

        # for col in self.full.columns:
        #     self.ts = pd.Series(self.full[col])
        #self.filled = self.full.fillna(method='ffill')
        #     self.full[col] = self.filled.values
            
        return




test = TAF('GRR')


#datetime.datetime.timestamp(datetime.datetime.utcnow())

#sns.set(rc={'figure.figsize':(11, 4)})
#s = test.df['wspd']
#print(s)
#s.plot(linewidth=0.5)            
