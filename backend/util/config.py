import os
from dotenv import load_dotenv

def read_env():
    load_dotenv()
    host = os.environ.get('server-host')
    port = int(os.environ.get('server-port'))
    dburl = os.environ.get('db-url')
    return host, port, dburl