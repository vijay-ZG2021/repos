import numpy as np
import pandas as pd
from pyxirr import xirr
from csvWriter import appendDFToCSV_void

def irr_calculate(position,prevpositions,cash):
    try:
        previndex = prevpositions.index
        prevvalue= prevpositions.at[previndex[0],'marketvalue'] * (-1)
        prevaccrued=prevpositions.at[previndex[0],'accruedamount'] * (-1)
        prevDate = prevpositions.at[previndex[0],'asofdate'] 
        currentvalue=position[0][1]

        fundid = position[0][4]
        arrDates =[]
        arrCash=[]
        arrInceptionCash=[]
        arrInceptionDates=[]
        if (prevvalue != 0.0 and currentvalue != 0.0):
            arrCash = np.array(prevvalue)    
            arrCash = np.append(arrCash,np.array(prevaccrued)) 
            arrDates = np.array(prevDate)
            arrDates = np.append(arrDates, np.array(prevDate))
            cash = cash.sort_values('expecteddate')
            for label,row in cash.iterrows():
                arrInceptionCash = np.append(arrInceptionCash,np.array(row['actualamount'])) 
                arrInceptionDates=np.append(arrInceptionDates,np.array(row['expecteddate']))
                if (row['expecteddate'] >= prevpositions.at[previndex[0],'asofdate'] and (row['expecteddate'] <= position[0][3])):
                    row_to_append = np.array(row['actualamount'])
                    arrCash = np.append(arrCash,row_to_append)
                    arrDates=  np.append(arrDates, np.array(row['expecteddate']))
            arrCash = np.append(arrCash, np.array(currentvalue))
            arrDates=  np.append(arrDates, np.array(position[0][3]))
            arrInceptionCash =  np.append(arrInceptionCash, np.array(currentvalue))
            arrInceptionDates = np.append(arrInceptionDates, np.array(position[0][3]))
        data  = calculate(position[0][0],fundid,arrCash,arrDates,arrInceptionCash,arrInceptionDates)
        df = pd.DataFrame(data=np.column_stack((arrDates,arrCash)),columns=['Date','Amount'])
        appendDFToCSV_void(df,'C:\TradeExport\Temp\supportingdata.csv',',')
        return data      
    except Exception as e:
        print('===================Failed in irr_calculate============')
        print(e)

def calculate(securityId,fundid,arrayCash,arrayDates,arrInceptionCash,arrInceptionDates):
    try:
        irr=0
        secxirr=0
        inceptionxirr=0
        result= []
        if np.any(arrayCash<0):
            if not np.isnan(arrayCash).any() and np.any(arrayCash<0):
                irr = np.irr(arrayCash)
                secxirr= xirr(arrayDates,arrayCash)

            if not np.isnan(arrInceptionCash).any() and len(arrInceptionCash)>2 and np.any(arrInceptionCash<0):
                inceptionxirr= xirr(arrInceptionDates,arrInceptionCash)
                
            if isinstance(inceptionxirr,(int,float)) and  isinstance(secxirr,(int,float)) and isinstance(irr,(int,float)):
                result = [fundid,int(securityId),round(irr*100,2),round(secxirr*100,2),round(inceptionxirr * 100,2)]
                #result = [fundid,int(securityId),irr,secxirr,inceptionxirr]
            else:
                result = [fundid,int(securityId),irr,secxirr,inceptionxirr]

        return result
    except Exception as e:
            print('===================Failed in irr_calculate============')
            print(e)