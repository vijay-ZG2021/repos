import configparser
import pandas as pd
from azure.storage.filedatalake import DataLakeServiceClient
from pathlib import Path

def download_Main(file_system:str,file_paths:list):
    '''
    file_system : name of the container
    file_paths: list of absolute paths to file in the file system
    '''
    try:
        name,creds = read_config()
        service_client = DataLakeServiceClient(
            account_url="{}://{}.dfs.core.windows.net".format("https", name),
            credential=creds,
        )

        file_system_client = service_client.get_file_system_client(
            file_system=file_system
        )

        for path in file_paths:
            download_file(file_system_client , path)
    except Exception as e:
        print("-----------------main in LoadFiles FAILED----------------")
        print(e)

def download_file(file_system_client, file_path):
    try:
        directories , file_name = parse_path(file_path)
        file_client = file_system_client.get_file_client(file_path)
        write_local_file(file_client , file_name)

                #read_file(file_name)
    except Exception as e:
        print("========================failed to get file client=========================")
        print(f'Invalid file path: {file_path}')
        print(e)

def write_local_file(file_client , file_name):
    try:
        download = file_client.download_file()
        downloaded_bytes = download.readall()
    except Exception as e:
        print("=========================failed to download file==========================")
        print(e)
    
    with open(file_name, "wb") as fd:  #binary content is written
        fd.write(downloaded_bytes)

def read_file(file_name):
    try:
        data = pd.read_csv(file_name,index_col=False)
        
        # data=[]
        # with open('Cash_2021-08-16.json') as f:
        #     for line in f.read().strip().splitlines():
        #         data.append(json.loads(line))

        # print(data)
        #cash = pd.read_csv("Cash_2021-08-17.csv",index_col=False)

        # headdata= data.head(6)
        # taildata=data.tail(9)
        # print(headdata)
        # print(taildata)


    except Exception as e:
        print("=========================failed to read file==========================")
        print(e)
    

def parse_path(path):
    
    file_names = path.split("/")
    if len(file_names) > 1:
        directories = file_names[:len(file_names)-1]  # all names except the last one are directories
        file_name = file_names[len(file_names)-1]
    else:
        # file in root
        directories = []
        file_name = path 

    return [directories , file_name]

def read_config():
    config = configparser.ConfigParser()
    config.read(Path(__file__).parent.joinpath("LoadFiles.config"))
    name = config.get("creds", "name")
    creds = config.get("creds", "creds")

    return name, creds


# if __name__ == "__main__":
    # container = "test-container"
    # file_paths = [
    #     "positions/positions_2021-08-16.csv",
    #     "Cash/Transactions/Cash_2021-08-17.csv"
    # ]
    #main(container , file_paths)
