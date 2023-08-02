from sqlalchemy import create_engine
from airflow.hooks.base import BaseHook
from airflow.models import Connection



# mysql connection
mysql_conn = Connection.get_connection_from_secrets('mysql_connection')
host = mysql_conn.host
username = mysql_conn.login
password = mysql_conn.password
dbtable = mysql_conn.schema
port = mysql_conn.port

# postgres connection
postgres_conn = Connection.get_connection_from_secrets('postgres_connection')
host_postgre = postgres_conn.host
username_postgre = postgres_conn.login
password_postgre = postgres_conn.password
dbtable_postgre = postgres_conn.schema
port_postgre = postgres_conn.port

def connect_mysql():
    engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{dbtable}')
    engine.connect()
    print('connect engine mysql')
    return  engine


def connect_postgres():
    engine = create_engine(f'postgresql://{username_postgre}:{password_postgre}@{host_postgre}:{port_postgre}/{dbtable_postgre}')
    engine.connect()
    print('connect engine Postgresql')
    return engine

