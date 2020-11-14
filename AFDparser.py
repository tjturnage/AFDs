"""
Extracting AFDs and sorting by time
"""


import re
from datetime import datetime

# https://mesonet.agron.iastate.edu/wx/afos/old.phtml

#url = "https://mesowest.utah.edu/cgi-bin/droman/meso_table_mesodyn.cgi?stn=MC093&unit=0&time=LOCAL&year1=&month1=&day1=0&hour1=00&hours=24&past=0&order=1"
#url = "https://kamala.cod.edu/mi/latest.fxus63.KGRR.html"
#url = "https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=1&glossary=0"



def cleanText(srcFile,dstFile):
    stripped = lambda s: "".join(i for i in s if 31 < ord(i) < 127)
    dst = open(dstFile, 'w')
    infile = open(srcFile, 'r')
    for lines in infile.readlines():
        fixed = stripped(str(lines))
        dst.write(fixed + '\n')
    dst.close()
    infile.close()


def get_line(section,searchstr):
    arr = section.split("\n")
    for a in range(0,len(arr)):
        test = arr[a]
        if searchstr in test:
            return test
        else:
            pass
    return None


def get_line_year(section):
    """
    Creates strings of current and previous years in order
    to find the line of text with date/time information. Previous year is
    included to ensure a complete list when AFDs straddle two years on and 
    immediately after New Year's Day.
    """
    current_year = datetime.now().strftime('%Y')
    previous_year = str(int(current_year) - 1)
    arr = section.split("\n")
    for a in range(0,len(arr)):
        test = arr[a]
        if(current_year in test):
            return test
        elif(previous_year in test):
            return test
        else:
            pass
    return None

try:
    from bs4 import BeautifulSoup
except:
    print("sant import!")
    
import requests
discussions =[]


for version in range(1,50):
    url = "https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=" + str(version) + "&glossary=0"
    try:
    	page = requests.get(url, timeout=5)
    	soup = BeautifulSoup(page.content, 'html.parser')
    	nws = soup.pre
    except:
        pass
    try:
        nwsStr = nws.string
        success = True
    except:
        success = False
    
    if success:
        getfid = nwsStr.split("$$")
        fcstr = get_line(getfid[1],"DISCUSSION")
        forecaster = fcstr.split("...")[1]
        all_sections = nws.string.split("&&")
        sections = all_sections[:-1]
        for s in range (0,len(sections)):
            section = sections[s]
            if "DISCUSSION" in section:
                issue_time = get_line_year(section)
                info = [issue_time, section, forecaster]
                #print(info)
                discussions.append(info)

                

uniqueList = []

separator = '  -------------  '


fout = open("/home/tjt/public_html/public/afds.txt","w")

for i in range(0,len(discussions)):
    issue_time = discussions[i][0]
    discussion = discussions[i][1]
    forecaster = discussions[i][2]
    
    if issue_time not in uniqueList:
        head = separator + forecaster + separator + "\n"
        text = head + discussion
        print(text)
        fout.write(text)
        uniqueList.append(issue_time)
        #finalList.append(sample)
                                


fout.close()

