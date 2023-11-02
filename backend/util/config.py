import os
from dotenv import load_dotenv

def read_env():
    load_dotenv()
    host = os.environ.get('SERVER-HOST')
    port = int(os.environ.get('SERVER-PORT'))
    dburl = os.environ.get('DB-URL')
    return host, port, dburl