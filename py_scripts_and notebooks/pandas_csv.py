import pandas as pd
import os

def choose_write_parameters(filepath):
    '''
        Determines the appropriate parameters for writing to a CSV file.

        If the specified file already exists, the function will return parameters to
        append the data to the existing file without writing the header. Otherwise,
        it will return parameters to create a new file and write the header.
    '''
    if os.path.isfile(filepath):
        # Append the data to the existing CSV file without writing the header
        mode = 'a'
        header = False
    else:
        mode = 'w'
        header = True
    return {
        'mode' : mode,
        'header' : header,
        'index' : False
        }

def get_prev_dir(dir:str):
    '''Returns previous directory path relatively to dir path'''
    prev_dir = dir[:dir.rfind("\\")+1]
    return prev_dir

def save_data(d:dict, filepath:str = None):
    '''
        Saves data to a csv file.

        If the specified file already exists, it appends the data to the existing file without writing the header. 
        Otherwise, it creates a new file and writes the header.
    '''
    if not filepath:
        cur_dir = os.getcwd()
        prev_dir = get_prev_dir(cur_dir)
        filepath = prev_dir + "data\\uncleaned_jobs.csv"
    print(f"Saving {len(d['job_id'])} rows to", filepath)
    params = choose_write_parameters(filepath)
    pd.DataFrame(d).to_csv(filepath, **params)

def load_from_csv(filepath:str, *column_names):
    """
        Loads data from a CSV file into a pandas DataFrame.

        If no column names are specified, all columns will be loaded.
        If specific column names are provided, only those columns will be loaded.
    """
    if len(column_names) == 0:
        return pd.read_csv(filepath, index_col=None)
    return pd.read_csv(filepath, usecols=column_names, index_col=None)

def delete_file(filepath:str):
    '''
        Deletes the specified file.

        It attempts to delete the file at the given filepath. If the file
        does not exist, a FileNotFoundError message is printed. If there is a permission
        issue, a PermissionError message is printed. Any other exceptions are caught
        and an error message is printed.
    '''

    try:
        os.remove(filepath)
        print(f"The file {filepath} has been deleted successfully.")
    except FileNotFoundError:
        print(f"The file {filepath} does not exist.")
    except PermissionError:
        print(f"Permission denied: unable to delete the file {filepath}.")
    except Exception as e:
        print(f"An error occurred while deleting the file {filepath}: {e}")
