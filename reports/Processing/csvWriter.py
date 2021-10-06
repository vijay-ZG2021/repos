import pandas as pd

def appendDFToCSV_void(df, csvFilePath, sep=","):
    import os
    import csv
    try:
        if not os.path.isfile(csvFilePath):
            df.to_csv(csvFilePath, mode='a', index=False, sep=sep,line_terminator='\n')
        elif len(df.columns) != len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns):
            raise Exception("Columns do not match!! Dataframe has " + str(len(df.columns)) + " columns. CSV file has " + str(len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns)) + " columns.")
        elif not (df.columns == pd.read_csv(csvFilePath, nrows=1, sep=sep).columns).all():
            raise Exception("Columns and column order of dataframe and csv file do not match!!")
        else:
            df.to_csv(csvFilePath, mode='a', index=False, sep=sep, header=False,line_terminator='\n')
        
        writer = open(csvFilePath,'a')
        writer.seek(0,2)
        writer.writelines('\r')

         
    except Exception as e:
        print('==============Failed to get Top 10 Holdings===============')
        print(e)