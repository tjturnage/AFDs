"""
Extracting AFDs and sorting by time
"""


import re
#import requests
import urllib

import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
#import matplotlib.gridspec as gridspec
#import seaborn as sns
#from bs4 import BeautifulSoup
from matplotlib import rcParams, cycler
import numpy as np
from matplotlib.lines import Line2D

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from datetime import datetime,timedelta
import os, sys
import shutil
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


#http://www.meteo.psu.edu/bufkit/data/GFS/12/gfs3_krqb.cobb
#http://www.meteo.psu.edu/bufkit/data/NAMNEST/12/namnest_krqb.cobb
#http://www.meteo.psu.edu/bufkit/data/NAM/12/nam_kgrr.cobb
#http://www.meteo.psu.edu/bufkit/data/RAP/03/rap_kgrr.cobb
#http://www.meteo.psu.edu/bufkit/data/HRRR/22/hrrr_kepo.cobb

try:
    os.listdir('/usr')
    scripts_dir = '/data/scripts'
except:
    scripts_dir = 'C:/data/scripts'
    sys.path.append(os.path.join(scripts_dir,'resources'))

#from my_nbm_functions import my_prods
AFD_dir = os.path.join(scripts_dir,'AFDS')

cat_colors = {'1': (1, 0, 1, 0.5),
              '2': (0.9, 0.1, 0.1, 0.5),
              '3': (0.9, 0.9, 0.1, 0.5),
              '4': (98/255, 147/255, 236/255 , 0.5),
              '5': (21/255, 174/255, 1/255, 0.5),
              '6': (8/255, 66/255, 1/255, 0.5),     
              }


class SnowTool:

    def __init__(self, station, model, download=True, plot=True):
        # the issuing office, not the TAF site
        self.stn = station
        self.model = model
        self.df = None
        self.df_master = None
        self.fig, self.ax = plt.subplots(1,1,sharex='row',figsize=(10,4))
        
        self.made_master = False
        self.plotted = False
        self.col = 1
        self.now = datetime.utcnow()

        #sorted(Path('C:/data/scripts').glob('*.txt'))
        self.raw_dir = 'C:/data/scripts/text'
        self.processed_dir = os.path.join(self.raw_dir,'processed')  
        self.staged_dir = os.path.join(self.raw_dir,'staged')
        for sf in os.listdir(self.staged_dir):
            os.remove(os.path.join(self.staged_dir,sf))
        self.main()


    def main(self):
        self.possible_files()   # build filenames to check for locally 
        self.get_files()        # downloads files determined to not already exist
        self.format_files()     # reformats to csv and writes to processed dir
        self.stage_files()      # stages processed files matching desired stn, model
        self.make_dataframe()   # makes dataframe for each model run, appends to df_master
        self.final_plot()       # plots df_master with accumulated models
        
    def possible_files(self):
        """
        Creates a list of filenames that would already exist if recent data
        were downloaded already.

        Returns
        -------
        None.

        """
        self.hrs = []
        self.psbl_files = []
        shift6 = (self.now.hour - 2)%6 + 2
        goback = self.now - timedelta(hours=2)
        goback6 = self.now - timedelta(hours=shift6)
        #clean = goback.replace(minute=0, second=0, microsecond=0)
        # hourly run time interval for these models, could go > 4 versions back
        if self.model == 'hrrr' or self.model == 'rap':
            
            for h in range (0,4):
                new = goback - timedelta(hours=h)
                hr = datetime.strftime(new, '%H')
                tf = datetime.strftime(new, '%Y%m%d_%H')
                psbl_file = '{}_{}_{}.txt'.format(tf,self.model,self.stn)
                self.psbl_files.append(psbl_file)
            self.hrs.append(hr)
            
        elif self.model == 'nam' or self.model == 'namnest' or self.model == 'gfs3':
            # 6 hourly run time interval for these models
            for i in range (0,4):
                new = goback6 - timedelta(hours=i*6)
                hr = datetime.strftime(new, '%H')
                tf = datetime.strftime(new, '%Y%m%d_%H')
                psbl_file = '{}_{}_{}.txt'.format(tf,self.model,self.stn)
                self.psbl_files.append(psbl_file)
        else:
            print('model not found!')

        print(self.psbl_files)
        return
    

    def get_files(self):
        self.already = os.listdir(self.processed_dir)

        for t in self.psbl_files:
            if t in self.already:
                if self.stn in t and self.model in t:
                    print('already exists: ' + str(t) )
                pass
            else:
                print('retrieving ... ' + str(t) )
                t2 = t.replace('txt','cobb')
                #20201219_12_gfs3_kmkg.cobb
                els = t2.split('_')[1:]
                #['12', 'gfs3', 'kmkg.cobb']
                hr = els[0]
                loc = els[2]
                if self.model == 'gfs3':
                    modup = 'GFS'
                else:
                    modup = self.model.upper()
                    
                #GFS/12/gfs3_krqb.cobb
                uri = '{}/{}/{}_{}'.format(modup,hr,self.model,loc)
                fout = '{}_{}_{}'.format(hr,self.model,loc)
                #http://www.meteo.psu.edu/bufkit/data/GFS/12/gfs3_krqb.cobb
                url = 'http://www.meteo.psu.edu/bufkit/data/' + uri

                fpath = os.path.join(self.raw_dir,fout)
 
                try:
                    print('downloading ... ' + url ) 
                    response = urllib.request.urlopen(url)
                    webContent = response.read()
                    f = open(fpath, 'wb')
                    f.write(webContent)
                    f.close()
                except:
                    print('could not download: ' + t)

        return

    def format_files(self):
        #find_model_name = re.compile('(?<=_)\S+(?=\.)')
        find_model_name = re.compile('(?<=_)\S+(?=_\S+\.)')
        find_dt = re.compile('\d{8}/\d{4}')

        files = sorted(Path(self.raw_dir).glob('*.cobb'))
        tmp = os.path.join('C:/data/scripts/text/processed', 'tmp.txt')
        for f in files:
            str(f).split('_')[2]
            mn = find_model_name.search(str(f))
            model_name=mn[0]

            need_time = True
            fp = Path(self.raw_dir).joinpath(f)

            with open(tmp, 'w') as fw:

                with open(fp) as f:
                    lines = f.readlines()
                    for l in lines:
                        line = str(l)
                        if need_time:
                            m = find_dt.search(line)
                            if m is not None:
                                issued = datetime.strptime(m[0],'%Y%m%d/%H%M')
                                ftime = datetime.strftime(issued, '%Y%m%d_%H')
                                need_time = False
                                fname = "{}_{}_{}.txt".format(ftime,model_name,self.stn)
 
                        if model_name != 'gfs3':
                            if 'FH' in line and 'FHR' not in line:
                                t = str(line).replace('|', ' ')
                                t2 = t.replace('          ', ' nowx ')
                                t3 = t2.replace(',', ' ')
                                t4 = t3.split()
                                t5 = t4[1:]
                                fw.write(', '.join(t5) + '\n')
                        else:
                            if '00Z' in line and 'FHr' not in line:
                                t = str(line).replace('|', ' ')
                                t2 = t.replace('          ', ' nowx ')
                                t3 = t2.replace(',', ' ')
                                t4 = t3.split()
                                t5 = t4[1:]
                                fw.write(', '.join(t5) + '\n')
                            
            shutil.move(tmp, os.path.join(self.processed_dir,fname))
        
        return

    def stage_files(self):
        already = os.listdir(self.processed_dir)
        for f in already:
            if self.stn in f and self.model in f:
                src = os.path.join(self.processed_dir,f)
                dst = os.path.join(self.staged_dir,f)
                shutil.copy(src, dst)
            else:
                pass

    def make_dataframe(self):
        self.trimmed_file_list= []
        self.colnames = []
        self.totnames = []
        self.df_master = None
        #globstr = '*{}*'.format(self.stn)
        #files = sorted(Path('C:/data/scripts/text/processed').glob(globstr))

        for f in os.listdir(self.staged_dir):
            fname = os.path.join(self.staged_dir,f)
            fhrs = None
            self.df = None
            find_dts = re.compile('\d{8}_\d{2}')
            #find_mod_name = re.compile('(?<=_)\S+(?=\.)')
            dts_m = find_dts.search(str(fname))
            dts = dts_m[0]
            if 'gfs' in str(fname):
                cols = ['FH', 'Wind','SfcT','Ptype','SRat','Snow','TotSF','TotSN','QPF','TotQPF', 'Sleet',
                        'TotPL','FZRA','TotZR','PcntSN','PcntPL','PcntRA']  
            else:
                cols = ['FH', 'Day', 'Mon','Date','Hour','Wind','SfcT','Ptype','Snow','TotSN','ObsSN','Sleet',
                'TotPL','FZRA','TotZR','QPF','TotQPF','SRat','CumSR','ObsSR','PcntSN','PcntPL','PcntRA','pcpPot','pthick']

            issued = datetime.strptime(dts, '%Y%m%d_%H')
            colname = datetime.strftime(issued, '%m%d%H')
            colname = colname + str(fname)[-7:-4]
            self.df = pd.read_csv(fname, names=cols)

    
            fhrs = list(self.df.FH.values)

            dts = []
            for fh in range(0,len(fhrs)):
                hrs = int(fhrs[fh])
                dt = issued + timedelta(hours=hrs)
                dts.append(dt)

            self.df['Datetime'] = dts
            try:
                self.df.drop(labels=['FH','Day','Mon','Date','Hour','pthick'],axis=1, inplace=True)
            except:
                pass
            self.df = self.df.set_index(pd.DatetimeIndex(self.df['Datetime']))
            self.df = self.df.rename_axis(None)

            #print(self.df['Snow'])
            if self.df_master is None:
                self.df_master = self.df
            
            sn = self.df['Snow'].astype(float)            
            self.df_master[str(colname)] = sn
            self.colnames.append(colname)

            totsn = self.df['TotSN'].astype(float)
            totname = 'tot' + colname
            self.df_master[str(totname)] = totsn
            self.totnames.append(totname)


        return


    def final_plot(self):
        #hours = mdates.HourLocator()
        #myFmt = DateFormatter("%d%h")
        self.N = len(self.totnames)
        cmap = plt.cm.Blues
        rcParams['axes.prop_cycle'] = cycler(color=cmap(np.linspace(0, 1, self.N)))

        # cat_colors = {'0': (212/255, 212/255, 212/255, 1),
        #       '1': (200/255, 200/255, 200/255, 1),
        #       '2': (175/255, 175/255, 175/255, 1),
        #       '3': (150/255, 150/255, 150/255, 1),
        #       '4': (125/255, 125/255, 150/255 , 1),
        #       '5': (100/255, 100/255, 150/255, 1),
        #       '6': (75/255, 75/255, 175/255, 1),     
        #       '7': (75/255, 75/255, 200/255, 1),
        #       '8': (75/255, 75/255, 225/255, 1),
        #       '9': (42/255, 42/255, 150/255, 1),
        #       '10': (200/255, 200/255, 200/255, 1),
        #       }        

        self.df_master['weighted'] = self.df_master[self.totnames[0]]

        x = 1
        for n in range(1,len(self.totnames)):
            self.df_master['weighted'] = self.df_master['weighted'] + self.df_master[self.totnames[n]] * (2 * n)
            x = x + (2 * n)

        self.df_master['weighted'] = self.df_master['weighted']/x
        c = 0.1
        #gap = 1/ (len(names) + 1)
        self.custom_line_list = []
        self.legend_title_list = []
        w = 3
        for n in self.totnames:
            self.leg = n[3:-3] + '00Z'
            #color = cat_colors[str(y)]
            #width = 2 + y/2
            #print(width)
            plt.plot(self.df_master[n], color=cmap(c), linewidth=w)
            self.custom_line = Line2D(self.df_master[n], [0], color=cmap(c), lw=w)
            self.legend_title_list.append(self.leg)
            self.custom_line_list.append(self.custom_line)

            c = c + 0.9/(self.N)
            w = w + 1

        self.weighted_line = Line2D(self.df_master['weighted'], [0], color='r', lw=2)
        self.custom_line_list.append(self.weighted_line)
        self.legend_title_list.append('Weighted Avg')
        plt.plot(self.df_master['weighted'], color='r',linewidth=2, linestyle='-',)
        plt.ylim(0, 2*np.max(self.df_master['weighted']) )
        plt.grid(axis='y')
        self.ax.legend(self.custom_line_list, self.legend_title_list)
        # place a text box in upper left in axes coords
        props = dict(boxstyle='round', facecolor='white', alpha=0.7)

        title_str = 'Snow Accum\nstation: {}\nmodel:  {}'.format(self.stn,self.model)
        self.ax.text(0.23, 0.95, title_str, transform=self.ax.transAxes, fontsize=14,
                     verticalalignment='top', bbox=props)


        self.ax.set_xlim(pd.Timestamp('2020-12-23 18:00:00'), pd.Timestamp('2020-12-26 06:00:00'))
        #self.ax.xaxis.set_major_locator(hours)
        #self.ax.xaxis.set_major_formatter(myFmt)
        return

#ktvc = SnowTool('ktvc','gfs3')
#mkg = SnowTool('kmkg','gfs3')
tvc = SnowTool('ktvc','gfs3')
#biv = SnowTool('biv','gfs3')
#buf = SnowTool('kbuf','gfs3')