import pandas as pd
from pandas.plotting import table
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import operator as o
import numpy as np
import pdfWriter
 
SMALL_SIZE=8
MEDIUM_SIZE=10
BIGGER_SIZE=12


def getProcessedData(positions,colType,fundName,fundNav):
    try:    
        positions= positions[~positions[colType].isnull()]
        grpPositions = positions.groupby([colType,'fundname'],as_index=False).sum()
        grpPositions = grpPositions[(grpPositions.fundname == fundName)]
        final = grpPositions[[colType,'fundname','marketvalue']] 
        lstData=[]
        for ind in final.index:
            fundname = final['fundname'][ind]
            if colType=="class" or colType=="subclass":
                marketvalue= final['marketvalue'][ind]/1000000
            else:
                marketvalue= final['marketvalue'][ind]/fundNav
               
            criteria = final[colType][ind]
            if criteria !='Not Applicable':
                lstData.append([fundname,criteria,round(marketvalue,3),colType])
      
        lstresult = [item for item in lstData if fundName in item]
        if len(lstresult)>2:
            df = pd.DataFrame(lstresult)
         
        return(df)
    except Exception as e:
        print('=============================Failed in Main')
        print(e)

def getFundNavinMillions(positions):
    fund_to_value = {}
    sumPositions= positions.groupby(['fundname'],as_index=False).sum()
    TotalMV = pd.DataFrame(sumPositions[['fundname','marketvalue']])
    for index,row in TotalMV.iterrows():
        fund_to_value [row['fundname']] = round(row['marketvalue']/1000000,1)     
    return fund_to_value

def showNAV(positions,prevpositions):
    funds = ['','CDO OPPORTUNITY','ZEPHYR RECOVERY MEZZ 2005-1','UNC','SBMA','PREMIA AMTRUST','ZEPHYR 8','INARI 2','LEVHY SCSp', 'INARI','PREMIA COOKE']
    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    
    currentVal= getFundNavinMillions(positions)
    prevVal= getFundNavinMillions(prevpositions)
    dfFund = pd.DataFrame(currentVal.items(),columns =['FundName','NAV'] )
    dfPrevFund = pd.DataFrame(prevVal.items(),columns =['FundName','NAV'] )
    try:
        dfFund['FundName'] = dfFund['FundName'].str.replace("ZAIS","").str.replace("FUND","")
     
        x = dfFund['FundName']
        y = dfFund['NAV']
        z= dfPrevFund['NAV']

        X_axis = np.arange(len(x))
        with PdfPages(r'C:\TradeExport\temp\Charts.pdf') as export_pdf:
            fig = plt.figure()
            ax = plt.subplot(2,1,1)
            #xlocs,xlabs = plt.xticks()
            #xlocs = [i+0.002 for i in range(0,10)]

            #rect1 = ax.bar(X_axis - 0.2, y,0.4,label = 'Current')
            #rect2 = ax.bar(X_axis + 0.2, z,0.4,label = 'Previous')
            fig.subplots_adjust(bottom = 0.2)
            ax.set_title("Total Fund NAV in millions")
            ax.set_xlabel("Funds")
            ax.set_ylabel('NAV')
            ax.legend()
            #ax.set_xticklabels((x),fontsize=4)
            ax.tick_params(axis='both', which='major', labelsize=4)
            for i, v in enumerate(y):
                ax.text(X_axis[i]-0.3,int(v)+10,str(int(v)))
                ax.text(X_axis[i]+0.1,int(z[i])+10,str(int(z[i])))
            dfs = pd.merge(left=dfFund, right=dfPrevFund,left_on='FundName',right_on='FundName')

            ax2 = plt.subplot(2,1,2)
            plt.axis('off')
            tbl= table(ax2,dfs,loc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(6)

            export_pdf.savefig()
            plt.close()
   
    except Exception as e:
        print("=========================failed to read file==========================")
        print(e)

def showType(positions,fundName):
    #Aggregate on Type
    try:
        aggType = positions.groupby(['type','fundname'],as_index=False).sum()
        aggMV = pd.DataFrame(aggType[['type','fundname','marketvalue']])
        aggMV['marketvalue'] = aggMV['marketvalue']/1000000
        Filter = (aggMV['fundname'] == fundName)
        aggMV = aggMV.loc[Filter,['type','fundname','marketvalue']]
        aggMV = aggMV.sort_values(['fundname','type'])
        aggMV.style.bar(subset = ['marketvalue'],color ='yellow')

    except Exception as e:
        print('=============================Failed in Main')
        print(e)
 

def showFundGraphs(positions,fundName,fundNav):
    try:
        row1 = positions.iloc[0]
        pdfWriter.setTitles(fundName,row1['asofdate'])

        dfData = getProcessedData(positions,"product",fundName,fundNav)
        pdfWriter.AddDftoPie(dfData,"product") 

        dfData = getProcessedData(positions,"capstructure",fundName,fundNav)
        pdfWriter.AddDftoPie(dfData,"capstructure")

        dfData = getProcessedData(positions, "class",fundName,fundNav)
        pdfWriter.AddDftoBar(dfData,"class")

        dfData = getProcessedData(positions,"subclass",fundName,fundNav)
        pdfWriter.AddDftoBar(dfData,"subclass")

        pdfWriter.printFigureArray(fundName)
    except Exception as e:
        print(e)
