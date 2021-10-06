import pandas as pd
import numpy as np
import csv


def main():
    try:
        #positions = read_file("positions_2021-08-16.csv")
        #prevpositions= read_file("positions_2021-06-16.csv")
        #cash = read_file("Cash_2021-08-17.csv")

        positions = pd.read_csv("positions_2021-08-16.csv")

        melt = pd.melt(positions,id_vars= 'description')
        melt.iloc[0:5,:]
        positions.describe()
        ct= pd.crosstab(positions['fund_name'],positions['type'])

        subset = positions[(positions['Market_value'] > 10000000)& (positions['Market_value']<15000000)]
        qry1 = positions.query('(fund_id==2) & (type=="Ledger")')
     
        groupd1 = positions.groupby(['fund_id','type']).aggregate(np.sum)

        for fundid, type1 in groupd1:
            if 208 in fundid:
                print(fundid)
                print(type1["Market_value"])
        key_list = groupd1.keys()
   
        for key,values in groupd1.iteritems():
            if key in key_list:
                print (key,values)
        # print(positions.columns)
        # print(groupd1.columns)


        # ndarray=np.array(positions)
        
        # #f= open("positions_2021-08-16.csv","r")
        # #position_list= list(csv.reader(f))
         
        # #Filter Fund
        # fund = ndarray[:,2]
        # fund_bool = fund == 2
        # oppfinal = ndarray[fund_bool] 

        # factor = oppfinal[:,10]
        # float_factor = factor.astype(np.float)
        # factor_bool = float_factor == 1.0
        # factor_final = oppfinal[factor_bool]
          
        # original = oppfinal[:,8]
        # original = original.astype(np.float)

        # current = original*float_factor
        # current = current[~np.isnan(current)]
        # print(current.sum())
        # # print(current.sum())
        # # currentnotional= positions[1:,9]
        # # print( current,currentnotional)

          

        
    except Exception as e:
        print('=============================Failed in Main')
        print(e)

def read_file(file_name):
    try:
        data = pd.read_csv(file_name,index_col=False,header=0)
        return data 
    except Exception as e:
        print("=========================failed to read file==========================")
        print(e)
  

main()