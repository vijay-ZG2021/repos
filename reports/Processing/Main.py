import numpy as np
import pandas as pd
import operator as o
from IRR import irr_calculate
import FundCalculator
from datetime import datetime
import datetime
import os
import sys
from LoadFiles import download_Main
import pandas as pd
from  csvWriter import appendDFToCSV_void
import FundGraphs

AZURE_CONTAINER = "test-container"
POSITION_FILE_PREFIX = "positions/positions_"
CASH_FILE_PREFIX = "Cash/Transactions/Cash_"
DIRECTORTYPATH = "C:\\Users\\vlakshmi\\source\\repos\\reports"

funds=[]
def clean_data(positions):
    funds_to_keep = ['CDO OPPORTUNITY','INARI FUND LP','SBMA','UNC','PREMIA AMTRUST 2017 AGGREGATE REINSURANCE TRUST','PREMIA B.D. COOKE GROUP QUOTA SHARE REINSURANCE TRUST','ZAIS INARI MASTER FUND 2  LTD','ZAIS LEVHY FUND I SCSp','ZEPHYR 7 MASTER FUND  LTD.','ZAIS ZEPHYR 8, LTD','ZEPHYR RECOVERY MEZZ 2005-1'] 
    if 'type' in positions.columns:
        positions = positions [(positions.type != 'Ledger')]
    #remove all CLO fund entries
    if 'fund_name' in positions.columns:
        positions.fund_name.isin(funds_to_keep)
        positions = positions[positions.fund_name.isin(funds_to_keep)]

    positions.columns= positions.columns.str.strip().str.lower()
    positions.columns = positions.columns.str.replace("_","")
    
    return positions

def newmain(strDate:str, file_mode : str ):
    try:
        validate_date(strDate) 
        
        if   file_mode != "Daily" and file_mode != "Monthly" and file_mode != "Quarterly":
            raise ValueError("file mode is either Daily or Monthly")

    except Exception as e:
        print('=============================Failed in Main================================')
        print(e)

    inputDateObj =  datetime.datetime.strptime(strDate, '%Y-%m-%d').date()
    if file_mode == "Daily":
        prevDate = inputDateObj - pd.DateOffset(days=1)   
    elif file_mode == "Monthly":
        prevDate = inputDateObj - pd.DateOffset(months=1) 
    elif file_mode == "Quarterly":
        prevDate = inputDateObj - pd.DateOffset(months=3) 

    #prevDateObj =  datetime.datetime.strptime(prevDate, '%Y-%m-%d').date()
    #remove_data_files()
    current_position_path = POSITION_FILE_PREFIX + inputDateObj.strftime("%Y-%m-%d") + ".csv"
    current_cash_path = CASH_FILE_PREFIX +  inputDateObj.strftime("%Y-%m-%d") + ".csv"
    previous_position_path = POSITION_FILE_PREFIX + prevDate.strftime("%Y-%m-%d") + ".csv"
    
    file_paths = [
        current_position_path,
        previous_position_path,
        current_cash_path]

    posFileName = "positions_"+ inputDateObj.strftime('%Y-%m-%d') + ".csv"
    prevFileName = "positions_"+ prevDate.strftime('%Y-%m-%d')+ ".csv"
    cashFileName = "Cash_" + inputDateObj.strftime('%Y-%m-%d')+ ".csv"
 
    if not os.path.isfile(DIRECTORTYPATH + "\\" + prevFileName):
            download_Main(AZURE_CONTAINER, file_paths) 
    
     
    processFiles(posFileName,prevFileName,cashFileName)
          

def validate_date(current_date:str) -> None:
    try:
        current_date = datetime.datetime.strptime(current_date, '%Y-%m-%d') #does not enforce zero padding
    except ValueError:
        raise ValueError('Incorrect date Format, should be YYYY-MM-DD')

def remove_data_files():
    data_files = [data_file for data_file in os.listdir('.') if
                 data_file.endswith('.csv')]

    for data_file in data_files:
        try:
            os.remove(data_file)
        except Exception as e:
            print("------------------Error in removing data file---------------------------")
            print(e)

def processFiles(position_file_name,prev_file_name,cash_file_name):
    try:
       
        pos = read_file( position_file_name)
        prevpos= read_file(prev_file_name)
        cash = read_file(cash_file_name)

        positions=  clean_data(pos)
        prevpositions = clean_data(prevpos)
        cash = clean_data(cash)

        funds = FundCalculator.getFundNAV(positions,prevpositions)
        #FundGraphs.showNAV(positions,prevpositions)
        for row in funds:
            if row[0]!='fundid':
                output=[]
                positions_df =    positions[(positions['fundid']== row[0])&(positions['type']!='Ledger')&(positions['type']!='Cash')]
                cash_df = cash[(cash['fundid']== row[0])]
                prevpositions_df = prevpositions[(prevpositions['fundid']==row[0])&(prevpositions['type']!='Ledger')&(prevpositions['type']!='Cash')]
                
                fundMV = round(row[2],2)
                #FundGraphs.showNAV(positions_df,prevpositions_df)
                #FundGraphs.showType(positions,row[1])
                FundCalculator.getTop10Holdings(positions_df,fundMV)
                FundCalculator.getTop10Issuers(positions_df,fundMV)
                FundGraphs.showFundGraphs(positions_df,row[1],row[2])
                
                #FundCalculator.writePositions(positions_df,prevpositions_df)
               
                #IRR Calculation
                result=calculate(row[0],positions_df,prevpositions_df,cash_df)
                df = pd.DataFrame(result,columns = ['fundid','securitymasterid','IRR','XIRR','InceptionXIRR'])
                fund_df = positions[(positions['fundid']==row[0])&(positions['type']=='Bond')]
               
                for sec in fund_df.iterrows():
                    secid =sec[1]['securitymasterid']
                    i = df[df['securitymasterid']==secid]
                    if not i.empty: 
                        output.append([sec[1]['fundid'],sec[1]['securitymasterid'],sec[1]['description'],i.iloc[0]['IRR'],i.iloc[0]['XIRR'],i.iloc[0]['InceptionXIRR']]) 
                newdf = pd.DataFrame(output, columns=['fundid','securitymasterid','description','IRR','XIRR','InceptionXIRR'])
                appendDFToCSV_void(newdf,'C:\\TradeExport\\Temp\\IRRresults.csv',',')

    except Exception as e:
        print('=============================Failed in Main')
        print(e)

def calculate(fund,positions,prevpositions,cash):
    try:
        filtered_df = positions[(positions['fundid']==fund)&(positions['type']=='Bond')]
        filtered_prevdf = prevpositions[(prevpositions['fundid']==fund)&(prevpositions['type']=='Bond')]
        
        result = []
        for label,row in filtered_df.iterrows():
            tmp=[]
            id = int(row['securitymasterid'])
            marketvalue= row['marketvalue']
            accrued = row['accruedamount']
            asofdate=row['asofdate']
            fundid=row['fundid']
            if (marketvalue != 0.0):
                lstPos = []
                lstPos.append([id,marketvalue,accrued,asofdate,fundid])
                tmpprevdf = filtered_prevdf[(filtered_prevdf['securitymasterid']==id)]
                tmpcashdf = cash[(cash['securitymasterid']==id)]
                if len(tmpprevdf)>0:
                    tmp = irr_calculate(lstPos,tmpprevdf,tmpcashdf)         
            if len(tmp)!=0:
                result.append(tmp)     
        return  result

    except Exception as e:
        print('=============================Failed in Main')
        print(e)

def read_file(file_name):
    try:
        if file_name.endswith(".csv"):
            data = pd.read_csv(file_name,index_col=False)
        elif file_name.endswith(".json"):
            data= pd.read_json(file_name,lines=True)
                
    except Exception as e:
        print("=========================failed to read file==========================")
        print(e)
    return data
 

if __name__=='__main__':
    num_args = len(sys.argv)-1
    if num_args==0:
        newmain('2021-09-07',"Daily")
    elif num_args>0 and num_args!=2:
        raise ValueError('Usage : python main.py <date> <file_mode>')
        sys.exit(1)
    else:
        newmain(sys.argv[1], sys.argv[2])
    
  


 