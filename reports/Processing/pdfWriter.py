import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import random
import operator as o
import numpy as np
 

SMALL_SIZE=8
MEDIUM_SIZE=10
BIGGER_SIZE=12

r=random.random()
g=random.random()
b=random.random()
fig1 = plt.figure(figsize=(8,8))
fig2 = plt.figure(figsize=(8,8))
fig3 = plt.figure(figsize=(16,10))


fundname=""
asofdate=""

def setTitles(fundname,asofdate):
    fundname = fundname
    asofdate=asofdate
 
def AddDftoTable(dfData,colType):
    try:
        if colType == "issuer":
            ax = fig3.add_subplot(211)
            ax.set_title("Top 10 Issuers")
        else:
            ax  = fig3.add_subplot(212)
            ax.set_title("Top 10 Holdings")
             
        the_table = ax.table(cellText=dfData.values,colLabels=dfData.keys(),loc='center',cellLoc='right',edges='open')
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(8)
        ax.axis('off')
        [i.set_linewidth(0.1) for i in ax.spines.itervalues(0)]
       
    except Exception as e:
        print(e)

def AddDftoPie(dfData,colType):
    try:
        if colType == "product":
            ax = fig1.add_subplot(221)
            ax2 = fig1.add_subplot(222)
        else:
            ax  = fig1.add_subplot(223)
            ax2 = fig1.add_subplot(224)

        fig1.tight_layout(pad=1.0)
        Filter =  ((dfData[3]== colType) &  (dfData[2]!=0.0))
        final = dfData.loc[Filter,[1,2]]
 
        my_colors = ['lightblue','lightyellow','lightsteelblue','silver','lightgrey','lightskyblue','gold','lightcoral']
        ax.set_title(colType)
        my_labels = final[1]
        ax.pie(final[2],labels=my_labels,autopct='%1.1f%%',shadow=True,startangle=90,normalize=False,colors=my_colors,radius=1,textprops={'fontsize': 6})
        ax.tick_params(axis='x', colors='blue')
         
        final[2]= round(100 * final[2],2)
        final.columns = [colType,'FundNav (%)']

 
        ax2.table(cellText=final.values,colLabels=final.keys(),loc='center',cellLoc='right')
        ax2.annotate('Report for '+ fundname + " as of" + asofdate, xy = (40, 85))
        ax2.axis('off')
        
    except Exception as e:
        print(e)


def AddDftoBar(dfData,colType):
    try:
        if colType == "class":
            ax = fig2.add_subplot(221)
            ax2 = fig2.add_subplot(222)
        else:
            ax  = fig2.add_subplot(223)
            ax2 = fig2.add_subplot(224)

        color= (r,g,b) 
        Filter = (dfData[3]== colType) 
        final = dfData.loc[Filter,[1,2]]
        X_axis = np.arange(len(final))
        
        ax.set_title(dfData[3][0] )
        ax.barh(final[1],final[2],color=color, height=0.54)
        ax.tick_params(axis='x', colors='blue' )
        ax.set_ylabel(colType )
        for i, v in enumerate(final[2]):
            ax.text(int(v)+3,X_axis[i]+0.1,str(int(v)))

        plt.margins(0.1)
        plt.subplots_adjust(left=0.15,bottom=0.2)
        
        final.columns = [colType,'FundNav (Mil)']
        ax2.table(cellText=final.values,colLabels=final.keys() ,loc='center',cellLoc='center')
        ax2.annotate('Report for '+ fundname + " as of" + asofdate, xy = (5, 5))
        ax2.axis('off')

    except Exception as e:
        print(e)

#def AddPositions(positions):    
    # positions= positions[~positions[colType].isnull()]
    # final = positions[[colType,'description','cusip','originalnotional','marketvalue']] 
    # ax3 = fig.add_subplot(223)
    # ax3.table(cellText=final.values,colLabels=final.keys(),loc='center',cellLoc='right')
     

def printFigureArray(fundName):
    pdf = PdfPages('C:\\TradeExport\\Temp\\'+fundName + ".pdf")
    for fig in range(1, plt.gcf().number + 1 ):  
        pdf.savefig(fig)
    pdf.close()
    plt.close(fig1)
    plt.close(fig2)
    plt.close(fig3)
    
