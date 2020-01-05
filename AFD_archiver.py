# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import shutil 
from datetime import datetime, timedelta


utcTime = datetime.utcnow()
delta = timedelta(hours=6)
nowTime = utcTime - delta

now_time_str = datetime.strftime(nowTime,'%Y%m%d_')


afd_dir = '/var/www/html/afds'
source = os.path.join(afd_dir,'afds.txt')

dst_fname = now_time_str + 'afds.txt'
destination = os.path.join(afd_dir,'archive',dst_fname)

shutil.copyfile(source, destination) 




