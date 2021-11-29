import pyodbc
import csv
import chardet
from shutil import copyfile
from datetime import datetime
#from typing import Any
import configparser
from pathlib import Path
import os
import sys

def upload_table(path,filename,delim,cursor,encoding):
    try:
        tbl = "[everest].[EquityRawdata]"
        cnt = 0
        cols=""
        with open(path+filename, 'r',encoding=encoding) as f:
            reader = csv.reader(f,delimiter =delim)
            for row in reader:
                row = ['NULL' if val=='' else val for val in row]
                row = [x.replace("'","''") for x in row]
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
       
    except Exception as e:
            print("--------------------Error------------------------")
            print(e)

def run_proc(cursor):
    try:
        values = (datetime.now().strftime('%Y-%m-%d'))
        sql = " EXEC [everest].[pr_processEquityAllocations] @report_file_date='"+values + "'"
        cursor.execute(sql)
        cursor.commit()
    except Exception as e:
            print("-------------------Error-------------------------")
            print(e)

def process_file(sourcepath,filename):
    now =datetime.now()
    date_time=now.strftime("%m%d%Y")
    copyfile(sourcepath+filename,sourcepath+"TradeCapture/"+filename+date_time+'.processed')
 
def get_connection():
    try:
        config = configparser.ConfigParser()

        if hasattr(sys, 'frozen'):
        # retrieve path from sys.executable
            path_current_directory = os.path.abspath(os.path.dirname(sys.executable))
        else:
        # assign a value from __file__
            path_current_directory = os.path.abspath(os.path.dirname(__file__))

        #path_current_directory = os.path.dirname(__file__)
        path_config_file = os.path.join(path_current_directory,  'LoadFile.config')
        config.read(path_config_file, encoding = 'utf-8-sig')
        #config.read(Path.dirname(Path.abspath("__file__")).parent.joinpath("LoadFile.config"),encoding = 'utf-8-sig')
        server = config.get("CoreContext","server")
        db=  config.get('CoreContext','database')
        user =  config.get('CoreContext','user')
        password = config.get('CoreContext','password')
        cnxn = pyodbc.connect('DRIVER={SQL Server Native Client 11.0};SERVER='+server+';DATABASE='+db+';UID='+user+';PWD='+ password)
        return cnxn

    except Exception as e:
            print("--------------------Error------------------------")
            print(e)
 
try:
    config = configparser.ConfigParser()

    if hasattr(sys, 'frozen'):
          # retrieve path from sys.executable
        path_current_directory = os.path.abspath(os.path.dirname(sys.executable))
    else:
        # assign a value from __file__
        path_current_directory = os.path.abspath(os.path.dirname(__file__))

    #path_current_directory = os.path.dirname(__file__)
    path_config_file = os.path.join(path_current_directory,  'LoadFile.config')
    config.read(path_config_file, encoding = 'utf-8-sig')
 
    sourcepath = config.get('CoreContext','sourcepath')
    filename = config.get('CoreContext','filename')
    f = open(sourcepath + filename,"rb")
    data = f.read()
    f.close()
    encoding = chardet.detect(data)['encoding']
    cnxn = get_connection()
    cursor = cnxn.cursor()

    upload_table(sourcepath,filename,",",cursor,encoding)
    run_proc(cursor)
    process_file(sourcepath,filename)

    cursor.close()
    cnxn.close()

except Exception as e:
        print("-------------------Error-------------------------")
        print(e)


