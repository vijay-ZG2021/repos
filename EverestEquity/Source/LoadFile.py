import pyodbc
import csv
import chardet
import pandas
from shutil import copyfile
from datetime import datetime
from typing import Any


def upload_table(path,filename,delim,cursor,encoding):
    try:
        tbl = "[everest].[EquityRawdata]"
        cnt = 0
        cols=""
        with open(path+filename, 'r',encoding=encoding) as f:
            reader = csv.reader(f,delimiter =delim)
            for row in reader:
                row.pop()
                row = ['NULL' if val=='' else val for val in row]
                #row = [x.replace("'","''") for x in row]
                if cnt==0:
                    cols =  ",".join(item for item in row) 
                    cols = cols.replace("'","")
                else:
                    out = "'" + "', '".join(str(item) for item in row) + "'"
                    out = out.replace("'NULL'",'NULL')
                
                if cnt != 0 :
                    query = "INSERT INTO " + tbl + "(" + cols+ ") VALUES (" + out + ")"
                    cursor.execute(query)
                cnt = cnt+1
                if cnt%10 == 0:
                    cursor.commit()
            cursor.commit()
            print("uploaded " + str(cnt) + " rows into table "+ tbl + ".")

    except Exception as e:
            print("--------------------------------------------")
            print(e)

def run_proc(procname,cursor,parameters):
    cursor.callproc(procname,parameters)

def process_file(sourcepath,destpath,filename):
    now =datetime.now()
    date_time=now.strftime("%m%d%Y")
    copyfile(sourcepath+filename,destpath+filename+date_time+'.processed')
 
#f = open ("//app-everestprod/EVERESTdownload/zais/Extracts/EquityTradeReport.csv","rb")
f = open ("C:/TradeExport/Extracts/TradesbyCounterparty-EquityOnly.csv","rb")
data = f.read()
f.close()
encoding = chardet.detect(data)['encoding']

server = 'SQL-Staging'
database= 'ZaisOperation'
username = "appuser"
password = 'zais4ppd3v'
# conn_str = (
#     r'DRIVER={SQL Server};'
#     r'SERVER=(local)\SQLEXPRESS;'
#     r'DATABASE=myDb;'
#     r'Trusted_Connection=yes;'
# )
cnxn = pyodbc.connect('DRIVER={SQL Server Native Client 11.0};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()

#upload_table("//app-everestprod/EVERESTdownload/zais/Extracts/","EquityTradeReport.csv",",",cursor,encoding)
#process_file("//app-everestprod/EVERESTdownload/zais/Extracts/","//app-everestprod/EVERESTdownload/zais/Extracts/TradeCapture/","EquityTradeReport.csv")

upload_table("C:/TradeExport/Extracts/","TradesbyCounterparty-EquityOnly.csv",",",cursor,encoding)
run_proc("[everest].[pr_processEquityAllocations]", cursor, datetime.now().strftime("%m%d%Y"))
process_file("C:/TradeExport/Extracts/","C:/TradeExport/Extracts/TradeCapture/","TradesbyCounterparty-EquityOnly.csv")

#upload_table("C:/TradeExport/Extracts/","DAILYZAISTCIMPORT.csv",",",cursor,encoding)
#run_proc("[everest].[pr_processAllocations]", cursor, datetime.now().strftime("%m%d%Y"))
#process_file("C:/TradeExport/Extracts/","C:/TradeExport/Extracts/TradeCapture/","EquityTradeReport.csv")

cursor.close()
cnxn.close()



