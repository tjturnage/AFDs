"""
Extracting AFDs and sorting by time
"""


import re
import requests
stns =['GRR','LAN','MKG']

import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter


from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from datetime import datetime,timedelta
import os, sys
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns


try:
    os.listdir('/usr')
    scripts_dir = '/data/scripts'
except:
    scripts_dir = 'C:/data/scripts'
    sys.path.append(os.path.join(scripts_dir,'resources'))

#from my_nbm_functions import my_prods
AFD_dir = os.path.join(scripts_dir,'AFDS')

# https://mesonet.agron.iastate.edu/wx/afos/old.phtml

#url = "https://mesowest.utah.edu/cgi-bin/droman/meso_table_mesodyn.cgi?stn=MC093&unit=0&time=LOCAL&year1=&month1=&day1=0&hour1=00&hours=24&past=0&order=1"
#url = "https://kamala.cod.edu/mi/latest.fxus63.KGRR.html"
#url = "https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=1&glossary=0"

class TAF:

    def __init__(self, station, issuedby, download=True, plot=True):
        self.station = station         # the issuing office, not the TAF site
        self.issuedby = issuedby    # the TAF site, not the issuing office 
                                    # welcome to opposite world !!
        self.download = download
        self.plot = plot
        self.sample = 'KDTW 092320Z 1000/1106 29004KT 6SM BR OVC028\nFM100200 32004KT 4SM BR SCT018 BKN030 OVC060\nFM100900 19004KT 3SM BR SCT008\nTEMPO 1009/1013 2SM BR BKN008\nFM101700 16008KT P6SM SCT150='



        self.columns = ['time', 'WDR', 'WSP','GST','VIS','FEW','SCT','BKN','OVC','VV', 'VCAT', 'CCAT']
        self.plot_cols = ['WSP','GST','VIS', 'BKN']
        #self.df = pd.DataFrame(index=self.idx,columns=self.columns)
        self.taf_dict = {}

        self.get_taf()
        self.clip_taf()
        self.fh_zero()
        
        self.parse_taf()
        self.finalize()
        self.plot_taf()
 

    def get_taf(self):
        not_yet = True
        for ver in range(1,20):
            if not_yet:
                url = "https://forecast.weather.gov/product.php?site={}&issuedby={}&product=TAF&format=ci&version={}&glossary=0".format(self.issuedby,self.station,ver)
                print(url)
                page = requests.get(url, timeout=4)
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
        #self.nwsStr = self.sample
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
            self.idx = pd.date_range(self.fhzero, periods=30, freq='30Min')
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
        self.v1 = re.compile('\d\/\d(?=SM)')   # _1/2_SM
        fraction_match = self.v1.search(str(self.line))

        self.v2 = re.compile('(?<=\s)\d\s.{3}(?=SM)')   # '_1_1/2SM
        int_match = self.v2.search(str(self.line))

        self.sm = re.compile('(?<=\s)\d(?=SM)')         # '3SM'
        single_match = self.sm.search(str(self.line))

        if fraction_match is not None:
            fraction = fraction_match[0]
            n = fraction.split('/')
            frac = int(n[0])/int(n[1])

            if int_match is not None:
                vint = int_match[0]
            else:
                vint = 0

            vis = vint + frac

        elif 'P6SM' in self.line:
            vis = 7            
        else:
            if single_match is not None:
                vis = int(single_match[0])
            else:
                print('no visibility found!')

        def fraction(self):
            n = self.fraction.split('/')
            return int(n[0])/int(n[1])

        if  vis < 0.5:
            vcat = 1

        elif vis < 1:
            vcat = 2

        elif vis < 2:
            vcat = 3

        elif vis < 3:
            vcat = 4

        elif vis <= 5:
            vcat = 6

        elif vis == 6:
            vcat = 7

        else:
            vcat = 9
            
 
        return vcat, vis
            
    
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
        self.skcm = re.compile('(?<=\s)SKC')   # '1 1/2SM
        mskc = self.skcm.search(self.line)    
        
        if mskc is not None:
            skc = True
        else:
            skc = False
            
        nullval = 0
        if mf is not None:
            few = int(mf[0])
        else:
            few =  nullval
            
        if ms is not None:
            sct = int(ms[0])
        else:
            sct =  nullval
            
        if mb is not None:
            bkn = int(mb[0])
        else:
            bkn = nullval
            
        if ob is not None:
            ovc = int(ob[0])
        else:
            ovc =  nullval
            
        if mvv is not None:
            vv = int(mvv[0])
        else:
            vv =  nullval
        
        #print(bkn,ovc)
        
        if ovc > bkn:
            cig_test = ovc
        else:
            cig_test = bkn

        if cig_test > nullval:
            if cig_test < 2:
                ccat = 1
            elif cig_test <= 4:
                ccat = 2
            elif cig_test < 7:
                ccat = 3
            elif cig_test < 10:
                ccat = 4
            elif cig_test < 20:
                ccat = 5
            elif cig_test <= 30:
                ccat = 6
            elif cig_test <= 60:
                ccat = 7
            elif cig_test <= 120:
                ccat = 8
        else:
            ccat = 9
        
        return ccat, skc,few,sct,bkn,ovc,vv

    def get_wind(self):
        windsearch = re.compile('(?<=\s)\S{3,}(?=KT)')   # _25020G30_KT  _25015_KT
        wm = windsearch.search(self.line)
        if wm is not None:
            wind = wm[0]
            try:
                wdir = int(wind[0:3])
            except:
                wdir = -1
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
            if 'TEMPO' in self.line:
                pass
            else:
                vt = self.get_time()
                wdir, ws, g = self.get_wind()
                vcat, vis = self.get_vis()
                ccat, skc, few, sct, bkn, ovc, vv = self.get_layers()
                arr = [vt,wdir,ws,g,vis,few,sct,bkn,ovc,vv,vcat,ccat]
                self.taf_arr.append(arr)

        return 



    def finalize(self):
        self.df = pd.DataFrame(self.taf_arr, columns=self.columns)
        self.df.set_index('time', inplace=True)
        self.few_ts = pd.Series(self.df['FEW'])
        self.few_fill = self.few_ts.reindex(index=self.idx,method='ffill')
        self.sct_ts = pd.Series(self.df['SCT'])        
        self.sct_fill = self.sct_ts.reindex(index=self.idx,method='ffill')
        self.bkn_ts = pd.Series(self.df['BKN'])
        self.bkn_fill = self.bkn_ts.reindex(index=self.idx,method='ffill')
        self.ovc_ts = pd.Series(self.df['OVC'])
        self.ovc_fill = self.ovc_ts.reindex(index=self.idx,method='ffill')
        self.vv_ts = pd.Series(self.df['VV'])
        self.vv_fill = self.vv_ts.reindex(index=self.idx,method='ffill')

        self.ccat_ts = pd.Series(self.df['CCAT'])
        self.ccat_fill = self.ccat_ts.reindex(index=self.idx,method='ffill')

        self.vcat_ts = pd.Series(self.df['VCAT'])
        self.vcat_fill = self.vcat_ts.reindex(index=self.idx,method='ffill')
        
        return

    
    def plot_taf(self):
        hours = mdates.HourLocator()
        # myFmt = DateFormatter("%d%h")
        # myFmt = DateFormatter("%d%b\n%HZ")
        # myFmt = DateFormatter("%I\n%p")
        # myFmt = DateFormatter("%I")    
        myFmt = DateFormatter("%d%H")
        
        #cig_labels = ['<200','<500','<700','<1K','<2K', '<3K', '<6K', '<12K',''],
        #vis_labels= ['0.25','0.5','1.0','2.0','','3', '6', '>6', '' ],
        fig, ax1 = plt.subplots(figsize=(12,8))
        ax1.set_xticks(self.idx)
        ax1.xaxis.set_major_locator(hours)
        #ax1.xaxis.set_major_formatter(myFmt)
        color = 'tab:red'
        ax1.set_ylabel('CIG', color=color)
        ax1.plot(self.ccat_fill,color=color,linewidth=0,marker=11, markersize=20)
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.set(yticks = [0, 1, 2, 3, 4, 5, 6, 7, 8 ,9])
        ax1.set(yticklabels = ['','<200','<500','<700','<1K','<2K', '<3K', '<6K', '<12K',''])
        plt.ylim(0,9)
        plt.grid(True)

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

        ax2.set_xticks(self.idx)
        ax2.xaxis.set_major_locator(hours)
        ax2.xaxis.set_major_formatter(myFmt)
        color = 'tab:blue'
        ax2.set_ylabel('VIS', color=color)
        ax2.plot(self.vcat_fill,color=color,linewidth=0,marker=10, markersize=15)
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set(yticks = [0, 1, 2, 3, 4, 5, 6, 7, 8 ,9])
        ax2.set(yticklabels = ['','< 1/2', '< 1', '< 2', '< 3', '< 4', '< 5', '6', 'P6', ''])
        plt.ylim(0,9)        
        plt.grid(True)



        self.image_file = self.station + '_TAF.png'
        self.image_dst_path = os.path.join(AFD_dir,self.image_file)
        plt.show()
        #plt.savefig(self.image_dst_path,format='png')
        #plt.close()
        return


test = TAF('ALS','PUB')


"""
KDTW 092320Z 1000/1106 29004KT 6SM BR OVC028
  FM100200 32004KT 4SM BR SCT018
  FM100900 19004KT 3SM BR SCT008
  TEMPO 1009/1013 2SM BR BKN008
  FM101700 16008KT P6SM SCT150
"""

"""
1: {'c': '<002',
    'v': '<1/2'}
2: {'c': '<002',
    'v': '<1/2'}

"""    


#datetime.datetime.timestamp(datetime.datetime.utcnow())

#sns.set(rc={'figure.figsize':(11, 4)})
#s = test.df['wspd']
#print(s)
#s.plot(linewidth=0.5)            
