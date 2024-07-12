import psycopg2


def get_conn_params():
    '''
    Reads "db_credentials.txt" file
    and returns data base credentials as dict object
    '''
    with open("db_credentials.txt") as f:
        conn_params = {}
        for line in f.readlines():
            key, value = line.strip().split("=")
            conn_params[key.strip()] = value.strip() 
    return conn_params


conn_params = get_conn_params()

def connect_to_db():
    '''
    Connects to a data base with credentials that are specified in the "db_credentials.txt" file
    and returns connector and cursor objects
    ''' 
    conn_params = get_conn_params()
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    return conn, cur


def create_table_if_not_exists(conn, cur, table_name = 'jobs_info'):
    sql_statement = f'''
    CREATE TABLE IF NOT EXISTS  {table_name} (
        job_id VARCHAR(20) PRIMARY KEY,
        job_title VARCHAR(150),
        company_name VARCHAR(150),
        location VARCHAR(150),
        published_date DATE,
        scraped_date DATE,
        is_polish_required  BOOLEAN,
        is_degree_required  BOOLEAN,
        position CHARACTER(30),
        technologies_found  TEXT,
        source VARCHAR(20),
        description TEXT
    );'''
    cur.execute(sql_statement)
    conn.commit()

def clear_table(conn, cur, table_name='jobs_info'):
    '''
    Deletes all rows from specified table
    '''
    # if we connector is closed, then open it, delete all rows and close it again
    close_needed = 0
    if conn.closed:
        close_needed = 1 
        conn, cur = connect_to_db(conn_params)
    cur.execute(f'DELETE  FROM {table_name};')
    conn.commit()
    if close_needed:
        cur.close()
        conn.close()


def get_headers(conn, cur):
    cur.execute("SELECT * FROM jobs_info LIMIT 1;")
    conn.commit()
    return [d[0] for d in cur.description]


def select_job_ids(conn, cur, source:str, table_name = 'jobs_info'):
    cur.execute(f"SELECT job_id FROM {table_name} WHERE source = '{source}';")
    conn.commit()
    return list(map(lambda tup: tup[0], cur.fetchall()))

