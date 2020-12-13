"""
Extracting AFDs and sorting by time
"""


import re
import requests

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


elements = ['wdr','wsp','gst','vis','vcat','vstr','few','sct','bkn','ovc','vv',
            'cig','ccat','lyr','wx']


taf_column_list = ['time']
ob_column_list = ['time']
taf_element_list = []
ob_element_list = []
taf_elements = {'k': 'v'}
ob_elements = {'o': 'u'}

for e in elements:
    taf_element_list.append(e)
    E = e.upper()
    taf_elements[e] = {'column':E}
    taf_column_list.append(E)
    oh = 'o' + str(e)
    ob_element_list.append(oh)
    OH = oh.upper()
    ob_elements[oh] = {'column':OH}
    ob_column_list.append(OH)



cat_colors = {'1': (1, 0, 1, 0.5),
              '2': (0.9, 0.1, 0.1, 0.5),
              '3': (0.9, 0.9, 0.1, 0.5),
              '4': (98/255, 147/255, 236/255 , 0.5),
              '5': (21/255, 174/255, 1/255, 0.5),
              '6': (8/255, 66/255, 1/255, 0.5),     
              }

cat_name = {'1':'VLIFR', '2':'LIFR', '3':'IFR', '4':'MVFR', '5':'VFR', '6':'VFR'}
levels = {'wdr':1, 
          'wsp':1.5,
          'gst':2,
          'vstr':2.5,
          'wx':3.1,
          'lyr':3.6,
          'cig':4,
          'cat':4.5}

olevels = {'owdr':1,
          'owsp':1.5,
          'ogst':2,
          'ovstr':2.5,
          'owx':3.1,
          'olyr':3.6,
          'ocig':4,
          'ocat':4.5}

null_val = 999

class TAF:

    def __init__(self, station, issuedby, download=True, plot=True):
        self.station = station         # the issuing office, not the TAF site
        self.issuedby = issuedby    # the TAF site, not the issuing office 
                                    # welcome to opposite world !!
        self.download = download
        self.plot = plot
        self.sample = 'KDTW 092320Z 1000/1106 29004KT 6SM BR OVC028\nFM100200 32004KT 4SM BR SCT018 BKN030 OVC060\nFM100900 19004KT 3SM BR SCT008\nTEMPO 1009/1013 2SM BR BKN008\nFM101700 16008KT P6SM SCT150='

        self.taf_columns = taf_column_list
        self.ob_columns = ob_column_list
        self.ob_arr = []
        self.now = datetime.utcnow()
        self.full_taf = self.get_taf()
        self.taf = self.clip_taf()
        self.fhzero = self.fh_zero()
        self.parse_taf()
        self.finalize()
        self.plot_xy()
        self.get_obs()
        self.ob_time()
        self.finalize_ob()
        self.plot_xy_ob()
 

    def get_obs(self):

        url = "https://aviationweather.gov/metar/data?ids=K{}&format=raw&date=&hours=12".format(self.station)
        print(url)
        page = requests.get(url, timeout=4)
        self.obs_soup = BeautifulSoup(page.content, 'html.parser')
        self.obs= self.obs_soup.find_all(['code'])
        return

    def ob_time(self):
        dhm = re.compile('\d{6}(?=Z\s)')
        for oh in self.obs:
            match = dhm.search(str(oh))
            if match is not None:
                d = int(match[0][0:2])
                h = int(match[0][2:4])
                m = int(match[0][4:6])
                self.observation_time = self.now.replace(day=d, hour=h, minute=m, second=0, microsecond=0)
                self.line = str(oh)
                wx = self.get_wx()
                print(wx)
                wdr, wsp, gst = self.get_wind()
                vcat, vis, vstr = self.get_vis()
                few, sct, bkn, ovc, vv, cig, ccat, lyr = self.get_layers()
                arr = [self.observation_time,wdr,wsp,gst,vis,vcat,vstr,few,sct,bkn,ovc,vv,cig,ccat,lyr,wx]
                self.ob_arr.append(arr)
        return
        

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
                        return self.nwsStr
                        #self.clip_taf()
                    else:
                        pass
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
    
            self.taf = '\n'.join(tmp2)
        else:
            print('could not clip!')
        return self.taf

    def fh_zero(self):
        dh = re.compile('(?<=\s)\d{5,}(?=Z\s)')
        mdh = dh.search(self.taf)
        if mdh is not None:
            dy = int(mdh[0][0:2])
            hr = int(mdh[0][2:4])
            self.issue_dt = self.now.replace(day=dy, hour=hr, minute=0, second=0, microsecond=0)
            self.fhzero = self.issue_dt + timedelta(hours=1)
            self.idx = pd.date_range(self.fhzero, periods=13, freq='H')

        else:
            print('can not find init time!')
        
        return self.fhzero



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
        self.find_fraction = re.compile('\d\/\d(?=SM)')   # _1/2_SM
        fraction_match = self.find_fraction.search(str(self.line))

        self.find_lone_int = re.compile('(?<=\s)\d(?=\s\d/\dSM)')   # '_1_1/2SM
        lone_int_match = self.find_lone_int.search(str(self.line))

        self.find_attached_int = re.compile('\d+(?=SM)')         # '3SM'
        attached_int_match = self.find_attached_int.search(str(self.line))


        if fraction_match is not None:
            fraction_str = fraction_match[0]
            n = fraction_str.split('/')
            fraction = int(n[0])/int(n[1])

            
            if lone_int_match is not None:
                lone_int_str = lone_int_match[0]
                lone_int = float(lone_int_str)
            else:
                lone_int_str = ''
                lone_int = 0

            vis_str = lone_int_str + ' ' + fraction_str
            vis = lone_int + fraction

        elif attached_int_match is not None:
            vis = int(attached_int_match[0])
            if vis >= 6:
                vis = 7    
                vis_str = 'P6'
            else:
                vis_str = str(vis)

        if vis < 0.5:
            vcat = 1
        elif vis < 1:
            vcat = 2
        elif vis < 3:
            vcat = 3
        elif vis <= 5:
            vcat = 4
        else:
            vcat = 5

        return vcat, vis, vis_str
            
    
    def get_layers(self):

        self.fewm = re.compile('(?<=FEW)\d{3}')   # 'FEW_040_'
        few_match = self.fewm.search(self.line)
        self.sctm = re.compile('(?<=SCT)\d{3}')   # 'SCT_040_'
        sct_match = self.sctm.search(self.line)
        self.bknm = re.compile('(?<=BKN)\d{3}')   # 'BKN_040_'   
        bkn_match = self.bknm.search(self.line)                
        self.ovcm = re.compile('(?<=OVC)\d{3}')   # 'OVC_040_'
        ovc_match = self.ovcm.search(self.line)    
        self.vvm = re.compile('(?<=VV)\d{3}')     # 'VV_004_'
        vv_match = self.vvm.search(self.line)    
 
        few = null_val    
        sct = null_val  
        bkn = null_val   
        ovc = null_val
        vv = null_val  
        
        if few_match is not None:
            few = int(few_match[0])
        if sct_match is not None:
            sct = int(sct_match[0])
        if bkn_match is not None:
            bkn = int(bkn_match[0])
        if ovc_match is not None:
            ovc = int(ovc_match[0])
        if vv_match is not None:
            vv = int(vv_match[0])
   

        if vv != null_val:
            cig = vv
        elif bkn != null_val:
            cig = bkn
        elif ovc != null_val:
            cig = ovc  
        else:
            cig = null_val
        

        if few != null_val:
            lyr = few
        elif sct != null_val:
            lyr = sct
        else:
            lyr = null_val
        

        if cig < 2:
            ccat = 1
        elif cig <= 4:
            ccat = 2
        elif cig < 10:
            ccat = 3
        elif cig <= 30:
            ccat = 4
        else:
            ccat = 5

        return few, sct, bkn, ovc, vv, cig, ccat, lyr

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
                g = null_val
                wsp = int(wind[-2:])
        return wdir, wsp, g


    def get_wx(self):
        wx_str = ''
        i = 0
        for w in ('TS','RA','SN','PL','BR','FG','VCTS','VCSH', 'UP'):
            if w in self.line:
                i = i + 1
                if i%2 == 0:
                    wx_str = wx_str + '\n' + w
                else:
                    wx_str = wx_str + w         
        return wx_str

    def parse_taf(self):
        self.taf_arr = []
        for self.line in self.taf.splitlines():
            if 'TEMPO' in self.line:
                pass
            else:
                wx = self.get_wx()
                print(wx)
                vt = self.get_time()
                wdr, wsp, gst = self.get_wind()
                vcat, vis, vstr = self.get_vis()
                few, sct, bkn, ovc, vv, cig, ccat, lyr = self.get_layers()
                arr = [vt,wdr,wsp,gst,vis,vcat,vstr,few,sct,bkn,ovc,vv,cig,ccat,lyr,wx]
                self.taf_arr.append(arr)
        return 




    def finalize_ob(self):
        self.otime_str = []
        self.odf = pd.DataFrame(self.ob_arr, columns=self.ob_columns)
        self.odf.set_index('time', inplace=True)
        self.odf.sort_index(inplace=True)
        t0 = self.odf.index[0]
        ob_init = t0.ceil(freq='H')
        timedelta = self.now - ob_init
        hours_ahead = int(timedelta.seconds/3600)

        self.odx = pd.date_range(ob_init, periods=hours_ahead, freq='H')
        self.ofew_ts = pd.Series(self.odf['OFEW'])

        self.ofew_fill = self.ofew_ts.reindex(index=self.odx,method='ffill')
        ob_elements['ofew']['data'] = self.ofew_fill.values.tolist()

        self.otimes = self.ofew_fill.index.values
        for t in range(0,len(self.otimes)):
            dt = pd.to_datetime(self.otimes[t]) 
            otstr = dt.strftime('%d.%H')
            self.otime_str.append(otstr)


        for e, c in zip(ob_element_list, ob_column_list[1:]):

            ts = pd.Series(self.odf[c])        
            ts_fill = ts.reindex(index=self.odx,method='ffill')
            ob_elements[e]['data'] = ts_fill.values.tolist()            

        return


    def finalize(self):
        self.time_str = []
        self.df = pd.DataFrame(self.taf_arr, columns=self.taf_columns)
        self.df.set_index('time', inplace=True)

        self.few_ts = pd.Series(self.df['FEW'])
        self.few_fill = self.few_ts.reindex(index=self.idx,method='ffill')
        taf_elements['few']['data'] = self.few_fill.values.tolist()

        self.times = self.few_fill.index.values
        for t in range(0,len(self.times)):
            dt = pd.to_datetime(self.times[t]) 
            tstr = dt.strftime('%d.%H')
            self.time_str.append(tstr)

        
        for e, c in zip(taf_element_list, taf_column_list[1:]):

            ts = pd.Series(self.df[c])        
            ts_fill = ts.reindex(index=self.idx,method='ffill')
            taf_elements[e]['data'] = ts_fill.values.tolist()            

        return


    def render(self):
        stuff = ['wdr','wsp','gst','vstr','wx','lyr','cig']
        for j in range(0,len(stuff)):
            el = stuff[j]
            dat = taf_elements[el]['data']
            for i in range(0,len(self.idx)):
                txt = dat[i]
                if str(txt) == str(null_val):
                    txt = ''
                else:
                    if el == 'vstr' or el == 'wx':
                        txt = txt
                    elif el == 'wsp' or el == 'gst':
                        txt = f'{txt:02}'
                    else:
                        txt = f'{txt:03}'
                    
                vcat = int(self.vcat_ts[i])
                ccat = int(self.ccat_ts[i])
                print(vcat,ccat)
                if vcat < ccat:
                    cat = vcat
                else:
                    cat = ccat
     
                col = cat_colors[str(cat)]
                self.ax1.bar(i, levels['cat']-0.1, self.width, color=col)

                plt.text(i,levels[str(stuff[j])],txt, dict(size=11),color='k', ha='center', va='center')
                plt.text(i,levels['cat'],cat_name[str(cat)], dict(size=11),color='k', ha='center',va='center')
        return
        


    def render_ob(self):
        ostuff = ['owdr','owsp','ogst','ovstr','owx','olyr','ocig']
        for j in range(0,len(ostuff)):
            el = ostuff[j]
            dat = ob_elements[el]['data']
            for i in range(0,len(self.odx)):
                txt = dat[i]
                if str(txt) == str(null_val):
                    txt = ''
                else:
                    if el == 'ovstr' or el == 'owx':
                        txt = txt
                    elif el == 'owsp' or el == 'ogst':
                        txt = f'{txt:02}'
                    else:
                        txt = f'{txt:03}'
                    
                ovcat = ob_elements['ovcat']['data'][i]
                occat = ob_elements['occat']['data'][i]
                if ovcat < occat:
                    ocat = ovcat
                else:
                    ocat = occat
     
                col = cat_colors[str(ocat)]
                #self.ax1.bar(i, levels['ocat']-0.1, self.width, color=col)
                self.ax1.bar(i, 6, self.width, color=col)

                plt.text(i,olevels[str(ostuff[j])],txt, dict(size=11),color='k', ha='center', va='center')
                plt.text(i,olevels['ocat'],cat_name[str(ocat)], dict(size=11),color='k', ha='center',va='center')
        return
        


    def plot_xy_ob(self):

        self.width = 0.9
        self.x = np.arange(0,len(self.odx))


        fig, self.ax1 = plt.subplots(figsize=(12,4))

        self.ax1.set(yticks = list(levels.values()))
        self.ax1.set(yticklabels = ['WDR','WSP','GST','VIS','WX','SCT','CIG', 'CAT'])
        plt.xticks(ticks=self.x,labels=self.otime_str)

        self.vcat_ts = ob_elements['ovcat']['data']
        self.ccat_ts = ob_elements['occat']['data']

        self.render_ob()
        
        plt.ylim(0,5.5)
        
        self.image_file = self.station + '_TAF.png'
        self.image_dst_path = os.path.join(AFD_dir,self.image_file)
        plt.show()
        #plt.savefig(self.image_dst_path,format='png')
        #plt.close()
        return


    def plot_xy(self):

        self.width = 0.9
        self.x = np.arange(0,len(self.idx))


        fig, self.ax1 = plt.subplots(figsize=(12,4))

        self.ax1.set(yticks = list(levels.values()))
        self.ax1.set(yticklabels = ['WDR','WSP','GST','VIS','WX','SCT','CIG', 'CAT'])
        plt.xticks(ticks=self.x,labels=self.time_str)

        self.vcat_ts = taf_elements['vcat']['data']
        self.ccat_ts = taf_elements['ccat']['data']

        self.render()
        
        plt.ylim(0,levels['cat']+0.5)
        
        self.image_file = self.station + '_TAF.png'
        self.image_dst_path = os.path.join(AFD_dir,self.image_file)
        plt.show()
        #plt.savefig(self.image_dst_path,format='png')
        #plt.close()
        return



test = TAF('TVC','APX')     # TAF, WFO



    # def plot_taf(self):
    #     hours = mdates.HourLocator()
    #     myFmt = DateFormatter("%d%H")

    #     fig, ax1 = plt.subplots(figsize=(12,8))
    #     ax1.set_xticks(self.idx)
    #     ax1.xaxis.set_major_locator(hours)
    #     #ax1.xaxis.set_major_formatter(myFmt)
    #     color = 'tab:red'
    #     ax1.set_ylabel('CIG', color=color)
    #     ax1.plot(self.ccat_fill,color=color,linewidth=0,marker=11, markersize=20)
    #     ax1.tick_params(axis='y', labelcolor=color)
    #     ax1.set(yticks = [0, 1, 2, 3, 4, 5, 6, 7, 8 ,9])
    #     ax1.set(yticklabels = ['','<200','<500','<700','<1K','<2K', '<3K', '<6K', '<12K',''])
    #     plt.ylim(0,6)
    #     plt.grid(True)

    #     self.image_file = self.station + '_TAF.png'
    #     self.image_dst_path = os.path.join(AFD_dir,self.image_file)
    #     plt.show()
    #     #plt.savefig(self.image_dst_path,format='png')
    #     #plt.close()
    #     return
