import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.transforms
from  csvWriter import appendDFToCSV_void
import pdfWriter

def writePositions(positions,prevpositions):
    try:
        mergedPos = pd.merge(positions,prevpositions, on =['fundid','securitymasterid','type','zaisid'])
        selectedCols = mergedPos.loc[:,["fundid","asofdate","type","description_x","cusip_x","originalnotional_x","price_y","price_x","pricesource_x","marketvalue_x","product","class","subclass"]]
        appendDFToCSV_void(selectedCols,'C:\\TradeExport\\Temp\\Positions.csv', sep=",") 
    except Exception as e:
        print('==============Failed in write Positions===============')
        print(e)


def getFundNAV(positions,prevpositions):
      #''''''--- Filter funds''''
    try:
        grpPositions = positions.groupby(['fundid','fundname'],as_index=False).sum()
        df = pd.DataFrame(grpPositions, columns = ["fundid","fundname","marketvalue"])
        funds = [df.columns.values.tolist()] + df.values.tolist()
        return funds
      
        #Fund Aggregate
        sumPositions= positions.groupby(['fund_name'],as_index=False).sum()
        TotalMV = pd.DataFrame(sumPositions[['fund_name','Market_value']])
        
        for index,row in TotalMV.iterrows():
            fund_to_value [row['fund_name']] = row['Market_value']/1000000
            lstFunds.append(row['fund_name'])

        return positions
    except Exception as e:
        print('==============Failed in NAV===============')
        print(e)

def getTop10Holdings(positions,fundMV):
    try:
                fund_df = positions.sort_values('marketvalue',ascending=False)
                fund_df['marketvalue'] = round(fund_df['marketvalue'].astype(np.float),2)
                fund_df['Net Weight %'] = round((fund_df['marketvalue']/fundMV),6)
                top10 = fund_df.head(10)
                newdf=pd.DataFrame(top10, columns=['fundname','cusip','description','marketvalue','class','Net Weight %'])
                appendDFToCSV_void(newdf,'C:\\TradeExport\\Temp\\Top10Holdings.csv', sep=",")    
                pdfWriter.newFigures
                pdfWriter.AddDftoTable(newdf,"Holdings")        
    except Exception as e:
        print('==============Failed to get Top 25 Holdings===============')
        print(e)

def getTop10Issuers(positions,fundMV):
    try:
                grp_issuer=positions.groupby(['fundname','issuername'],as_index=False)['marketvalue'].sum()
                grp_issuer = grp_issuer.sort_values('marketvalue',ascending=False)
                grp_issuer['marketvalue'] = round(grp_issuer['marketvalue'].astype(np.float),2)
                grp_issuer['Net Weight %'] = round((grp_issuer['marketvalue']/fundMV)* 100,2)
                top10 = grp_issuer.head(10)
                newdf=pd.DataFrame(top10, columns=['fundname','issuername','marketvalue','Net Weight %'])
                appendDFToCSV_void(newdf,'C:\\TradeExport\\Temp\\Top10Issuer.csv', sep=",")
                pdfWriter.AddDftoTable(newdf,"issuer") 
    except Exception as e:
        print('==============Failed to get Top 10 Holdings===============')
        print(e)

 