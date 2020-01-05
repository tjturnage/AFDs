# -*- coding: utf-8 -*-
"""
Extracting AFDs and sorting by time
"""


import re
from datetime import datetime

# https://mesonet.agron.iastate.edu/wx/afos/old.phtml

#url = "https://mesowest.utah.edu/cgi-bin/droman/meso_table_mesodyn.cgi?stn=MC093&unit=0&time=LOCAL&year1=&month1=&day1=0&hour1=00&hours=24&past=0&order=1"
#url = "https://kamala.cod.edu/mi/latest.fxus63.KGRR.html"
#url = "https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=1&glossary=0"

def issueTime(section):
    reg = re.compile('\d\d\d.*\s20\d\d')
    m = re.search(reg, section)
    dateStr = m.group(0)
    issued = datetime.strptime(dateStr, "%H%M %p %Z %a %b %d %Y")
    return str(issued)

def cleanText(srcFile,dstFile):
    stripped = lambda s: "".join(i for i in s if 31 < ord(i) < 127)
    dst = open(dstFile, 'w')
    infile = open(srcFile, 'r')
    for lines in infile.readlines():
        fixed = stripped(str(lines))
        dst.write(fixed + '\n')
    dst.close()
    infile.close()

def identifyFcstr(fcstrSec):
    dictFcstrs = {}
    mets = fcstrSec.split('\n')
    for metName in range(0,len(mets)):
        fcstLine = mets[metName]
        ids = fcstLine.split('...')
        if len(ids) > 1:
            dictFcstrs[ids[0]] = ids[1]
    if 'SHORT TERM' in dictFcstrs:
        dictFcstrs['DISCUSSION'] = 'NA'
    return dictFcstrs



from bs4 import BeautifulSoup
import requests

for version in range(1,50):
    if version < 10:
        verStr = "0" + str(version)
    else:
        verStr = str(version)
    
    url = "https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=" + str(version) + "&glossary=0"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    nws = soup.pre
    nwsStr = nws.string
#section_lines = [line for line in nwsStr.split('\n') if "DISCUSSION" in line]
#print section_lines
    sections = nws.string.split("&&")

srcFile = '2019-02-AFDs.txt'
fixedFile = 'fixed2.txt'
cleanText(srcFile, fixedFile)
separator = '  ----------------------  '
masterList = []
fnum = {'04': 'Felver', 'MJS': 'Sekelsky', 'TJT': 'Turnage', 'Borchardt': 'Borchardt',
        'Ostuno': 'Ostuno' }

if 2 > 1:
    again = open(fixedFile, 'r')
    data_read = again.read()
    dataStr = str(data_read)
    #print(dataStr)
    afds = dataStr.split('AFDGRR')
    for a in range(0,len(afds)):
        thisAFD = afds[a]
        getfids = thisAFD.split("$$")
        if len(getfids) > 0:
            fids = getfids[-1]
            fdict = identifyFcstr(fids)
            
            justAFD = getfids[0]
            getSecs = thisAFD.split("&&")
            for sec in range(0,len(getSecs)):
                s = getSecs[sec]
                if len(getSecs[sec]) > 0:  
                    if re.compile("\.UPDATE...").search(s,1):
                        tStamp = issueTime(s)
                        secType = '4-update'
                        fcstr = fdict['UPDATE']
                        masterList.append([tStamp,secType,fcstr,s])
                    elif re.compile("\.DISCUSSION...").search(s,1):
                        tStamp = issueTime(s)
                        secType = '2-discussion'
                        fcstr = fdict['DISCUSSION']
                        masterList.append([tStamp,secType,fcstr,s])
                    elif re.compile("\.AVIATION...").search(s,1):
                        tStamp = issueTime(s)
                        secType = '3-aviation'
                        fcstr = fdict['AVIATION']      
                        masterList.append([tStamp,secType,fcstr,s])
                    elif re.compile("Synopsis").search(s,1):
                        tStamp = issueTime(s)
                        justSyn = s.split('.SYNOPSIS...')
                        s = '\n\n.SYNOPSIS...\n' + justSyn[1]
                        secType = '1-synopsis'
                        fcstr = fdict['SYNOPSIS']
                        masterList.append([tStamp,secType,fcstr,s])
                    else:
                        pass


    uniqueList = []
    finalList = []
    
    # eliminate duplicates
    for i in range(0,len(masterList)):
        sample = masterList[i]
        check = sample[0] + sample[1]
        if check not in uniqueList:
            uniqueList.append(check)
            finalList.append(sample)
                                
    finalSorted = sorted(finalList, reverse=True)
    
    complete = open('complete.txt', 'w')
    for j in range(0,len(finalSorted)):
        thisText = finalSorted[j]
        times = str(thisText[0])
        secType = str(thisText[1])        
        fcstr = str(thisText[2])
        text = str(thisText[3])
        
        #if ((fcstr == 'TJT') and ((secType == '2-discussion') or (secType == '1-synopsis'))):
        if (secType != '3-aviatondiscussion'):
            justThese = "   " + separator + fcstr + separator + text
            complete.write(justThese)
    
complete.close()