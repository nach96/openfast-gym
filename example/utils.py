import sys
import os

import beepy
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def name_date(name,extension=".csv"):
        from datetime import datetime
        now = datetime.now()
        date_time = now.strftime("%m_%d_%Y_%H_%M_%S")
        file_name = name + "_" + date_time + extension
        return file_name
    
def get_file_path(file_rel_path):
    file_path = os.path.join(os.path.dirname(__file__), file_rel_path)
    return file_path

def log_and_exit(myLog, id):
    # Plot Logged variables during training
    log_Path = get_file_path("../Logs/"+str(id))
    log_df = pd.DataFrame(myLog)
    log_df.to_csv(name_date(log_Path), sep=',', encoding='utf-8')