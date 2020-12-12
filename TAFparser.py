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



taf_elements = {'vis': {'1':1, '2':2, '3':3, '4':4, '5':4, '6':4, '7':4, '8':4, '9':4},
                'few': {'1':3, '2':4, '3':5, '4':6, '5':7, '6':8, '7':9, '8':9, '9':9},
                'sct': {'1':3, '2':4, '3':5, '4':6, '5':7, '6':8, '7':9, '8':9, '9':9},
                'bkn': {'1':3, '2':4, '3':5, '4':6, '5':7, '6':8, '7':9, '8':9, '9':9},
                'ovc': {'1':3, '2':4, '3':5, '4':6, '5':7, '6':8, '7':9, '8':9, '9':9},
                'vv': {'1':3, '2':4, '3':5, '4':6, '5':7, '6':8, '7':9, '8':9, '9':9},
                'vstr': {'1':3, '2':4, '3':5, '4':6, '5':7, '6':8, '7':9, '8':9, '9':9},
                'vcat': {'level':{'1':1, '2':2, '3':3, '4':4, '5':4, '6':4, '7':4, '8':4, '9':4}},
                'ccat': {'level':{'1':4, '2':5, '3':6, '4':7, '5':8, '6':9, '7':10, '8':10, '9':10}}
                }

cat_colors = {'1': (1, 0, 1, 1),
              '2': (1, 0, 0.6, 1),
              '3': (1, 0, 0.2, 1),
              '4': (1, 0, 0, 1),
              '5': (1, 0.5, 0.2, 1),
              '6': (0.4, 0.7, 1, 1),
              '7': (0.3, 0.6, 0.3, 1),
              '8': (0.2, 0.8, 0.2, 1),
              '9': (0.1, 0.9, 0.1, 1),
              '10': (0, 1, 0, 1),              
              }


class TAF:

    def __init__(self, station, issuedby, download=True, plot=True):
        self.station = station         # the issuing office, not the TAF site
        self.issuedby = issuedby    # the TAF site, not the issuing office 
                                    # welcome to opposite world !!
        self.download = download
        self.plot = plot
        self.sample = 'KDTW 092320Z 1000/1106 29004KT 6SM BR OVC028\nFM100200 32004KT 4SM BR SCT018 BKN030 OVC060\nFM100900 19004KT 3SM BR SCT008\nTEMPO 1009/1013 2SM BR BKN008\nFM101700 16008KT P6SM SCT150='



        self.columns = ['time','WDR','WSP','GST','VIS',
                        'FEW','SCT','BKN','OVC','VV',
                        'VCAT','CCAT','VSTR']
        #self.df = pd.DataFrame(index=self.idx,columns=self.columns)
        self.taf_dict = {}

        self.get_taf()
        self.clip_taf()
        self.fh_zero()
        
        self.parse_taf()
        self.finalize()
        self.plot_xy()
 


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
            self.idx = pd.date_range(self.fhzero, periods=15, freq='60Min')
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
        vis_frac_match = self.v1.search(str(self.line))

        self.v2 = re.compile('(?<=\s)\d(?=\s\d/\dSM)')   # '_1_1/2SM
        vis_lone_int_match = self.v2.search(str(self.line))

        self.sm = re.compile('(?<=\s)\d(?=SM)')         # '3SM'
        vis_normal_int_match = self.sm.search(str(self.line))

        if vis_frac_match is not None:
            fraction_str = vis_frac_match[0]
            n = fraction_str.split('/')
            fraction = int(n[0])/int(n[1])

            
            if vis_lone_int_match is not None:
                lone_int_str = vis_lone_int_match[0]
                lone_int = float(lone_int_str)
            else:
                lone_int_str = ''
                lone_int = 0

            vis_str = lone_int_str + ' ' + fraction_str
            vis = lone_int + fraction

        elif 'P6SM' in self.line:
            vis = 7
            vis_str = 'P6'
        else:
            if vis_normal_int_match is not None:
                vis_str = vis_normal_int_match[0]
                vis = int(vis_str)

            else:
                print('no visibility found!')

        if  vis < 0.5:
            vcat = 1
            
        elif vis < 1:
            vcat = 2

        elif vis < 2:
            vcat = 3

        elif vis < 3:
            vcat = 4

        elif vis <= 5:
            vcat = 5

        elif vis == 6:
            vcat = 6

        else:
            vcat = 7

        return str(vcat), vis, vis_str
            
    
    def get_layers(self):
        #self.skcm = re.compile('(?<=\s)SKC')# '1 1/2SM
        #mskc = self.skcm.search(self.line)   

        #self.skcm = re.compile('(?<=\s)SKC')# '1 1/2SM

        self.fewm = re.compile('FEW\d{3}')   # '1 1/2SM
        few_match = self.fewm.search(self.line)

        self.sctm = re.compile('SCT\d{3}')   # '1 1/2SM
        sct_match = self.sctm.search(self.line)

        self.bknm = re.compile('BKN\d{3}')   # '1 1/2SM    
        bkn_match = self.bknm.search(self.line)                

        self.ovcm = re.compile('OVC\d{3}')   # '1 1/2SM    
        ovc_match = self.ovcm.search(self.line)    


        self.vvm = re.compile('VV\d{3}')   # '1 1/2SM
        vv_match = self.vvm.search(self.line)    
 
        
        if few_match is not None:
            few_str = few_match[0]
        else:
            few_str = ''

        if sct_match is not None:
            sct_str = sct_match[0]
        else:
            sct_str = ''
            
        if bkn_match is not None:
            bkn_str = bkn_match[0]
        else:
            bkn_str = ''

        if ovc_match is not None:
            ovc_str = ovc_match[0]
        else:
            ovc_str = ''            

        if vv_match is not None:
            vv_str = vv_match[0]
        else:
            vv_str = ''        

        if vv_str != '':
            cig = int(vv_str[2:])
        elif bkn_str != '':
            cig = int(bkn_str[3:])
        elif ovc_str != '':
            cig = int(ovc_str[3:])   
        else:
            cig = 999
            

        if cig < 2:
            ccat = 1
        elif cig <= 4:
            ccat = 2
        elif cig < 7:
            ccat = 3
        elif cig < 10:
            ccat = 4
        elif cig < 20:
            ccat = 5
        elif cig <= 30:
            ccat = 6
        elif cig <= 60:
            ccat = 7
        elif cig <= 120:
            ccat = 8
        else:
            ccat = 9

        
        return few_str, sct_str, bkn_str, ovc_str, vv_str, str(ccat)

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
                wsp = int(wind[3:5])
                g = int(wind[-2:])
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
                vcat, vis, vstr = self.get_vis()
                few, sct, bkn, ovc, vv, ccat = self.get_layers()
                arr = [vt,wdir,ws,g,vis,few,sct,bkn,ovc,vv,vcat,ccat,vstr]
                self.taf_arr.append(arr)

        return 



    def finalize(self):
        self.df = pd.DataFrame(self.taf_arr, columns=self.columns)
        self.df.set_index('time', inplace=True)
        self.few_ts = pd.Series(self.df['FEW'])
        self.few_fill = self.few_ts.reindex(index=self.idx,method='ffill')
        taf_elements['few']['data'] = self.few_fill.values.tolist()

        self.sct_ts = pd.Series(self.df['SCT'])        
        self.sct_fill = self.sct_ts.reindex(index=self.idx,method='ffill')
        taf_elements['sct']['data'] = self.sct_fill.values.tolist()

        self.bkn_ts = pd.Series(self.df['BKN'])
        self.bkn_fill = self.bkn_ts.reindex(index=self.idx,method='ffill')
        taf_elements['bkn']['data'] = self.bkn_fill.values.tolist()


        self.ovc_ts = pd.Series(self.df['OVC'])
        self.ovc_fill = self.ovc_ts.reindex(index=self.idx,method='ffill')
        taf_elements['ovc']['data'] = self.ovc_fill.values.tolist()

        self.vv_ts = pd.Series(self.df['VV'])
        self.vv_fill = self.vv_ts.reindex(index=self.idx,method='ffill')
        taf_elements['vv']['data'] = self.vv_fill.values.tolist()

        self.ccat_ts = pd.Series(self.df['CCAT'])
        self.ccat_fill = self.ccat_ts.reindex(index=self.idx,method='ffill')
        taf_elements['ccat']['data'] = self.ccat_fill.values.tolist()
        taf_elements['bkn']['cat'] = self.ccat_fill.values.tolist()
        taf_elements['ovc']['cat'] = self.ccat_fill.values.tolist()


        self.vcat_ts = pd.Series(self.df['VCAT'])
        self.vcat_fill = self.vcat_ts.reindex(index=self.idx,method='ffill')
        taf_elements['vcat']['data'] = self.vcat_fill.values.tolist()
 

        self.vis_ts = pd.Series(self.df['VIS'])
        self.vis_fill = self.vis_ts.reindex(index=self.idx,method='ffill')
        taf_elements['vis']['data'] = self.vis_fill.values.tolist()      

        self.vstr_ts = pd.Series(self.df['VSTR'])
        self.vstr_fill = self.vstr_ts.reindex(index=self.idx,method='ffill')
        taf_elements['vstr']['data'] = self.vstr_fill.values.tolist()      


        return


    def render(self):
        if self.p == 'vstr':
            cats = taf_elements['vcat']['data']
            levels= taf_elements['vcat']['level']
        else:
            cats = taf_elements['ccat']['data']            
            levels = taf_elements['ccat']['level']            

        for i in range(0,15):
            print(self.ts[i])

            print(i,self.ts[i])
            cat = cats[i]
            level = levels[cat]
            col = cat_colors[cat]
            
            plt.text(i,level,str(self.ts[i]), dict(size=10),color=col)
        return
        

    def plot_xy(self):
        x = np.arange(0,len(self.idx)+1)
        #y = np.arange(1,13)

        fig, ax1 = plt.subplots(figsize=(12,8))
        ax1.set_xticks(x)
        ax1.set_ylabel('CIG')

        self.stuff = ['few','sct','bkn','ovc','vstr']
        self.vcat_ts = taf_elements['vcat']['data']
        self.ccat_ts = taf_elements['ccat']['data']
        for self.p in self.stuff:

            self.el = taf_elements[self.p]
            #print(taf_elements['ovc']['cat'])


            self.ts = taf_elements[self.p]['data']
            print(self.ts)
            #self.level = 3#taf_elements[p]['level']
            self.render()


        plt.ylim(1,12)


        
        self.image_file = self.station + '_TAF.png'
        self.image_dst_path = os.path.join(AFD_dir,self.image_file)
        plt.show()
        #plt.savefig(self.image_dst_path,format='png')
        #plt.close()
        return


    
    def plot_taf(self):
        hours = mdates.HourLocator()
        # myFmt = DateFormatter("%d%h")
        # myFmt = DateFormatter("%d%b\n%HZ")
        # myFmt = DateFormatter("%I\n%p")
        # myFmt = DateFormatter("%I")    
        myFmt = DateFormatter("%d%H")

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


test = TAF('TVC','APX')     # TAF, WFO


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
