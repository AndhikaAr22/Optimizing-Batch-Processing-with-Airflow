import requests
import pandas as pd 
import numpy as np
import logging
from connector.connection import connect_mysql, connect_postgres
from airflow.models import Variable


# fuction from getting data from api
def get_data():
    url = Variable.get("url_covid")
    respons = requests.get(url)
    result = respons.json()['data']['content']
    df = pd.json_normalize(result)
    logging.info("Data from api to dataframe ready")
    return df

# fuction for insert data from api to datalake(mysql)
def insert_raw_data():
    mysql_aunt = connect_mysql()
    data = get_data()
    print(data.info())

    data.to_sql(name='covid_raw_data', con=mysql_aunt, if_exists="replace", index=False)


# function for getting data from data lake
def get_data_lake_covid():
    mysql_aunt = connect_mysql()
    query = "select * from covid_raw_data"
    df_data = pd.read_sql(query, con=mysql_aunt)
    return df_data

# fuction create dimension province table and insert data from data lake to data warehouse
def create_dim_province():
    postgres_aunt = connect_postgres()
    df = get_data_lake_covid()
    df_dim_province = df[['kode_prov', 'nama_prov']]
    df_dim_province = df_dim_province.rename(columns={'kode_prov':'province_id', 'nama_prov':'province_name'})
    df_dim_province = df_dim_province.drop_duplicates()
    df_dim_province.to_sql(name='dim_province', con=postgres_aunt, index=False, if_exists='replace')
    logging.info("insert data dim_province to dwh postgres success")

# fuction create dimension district table and insert data from data lake to data warehouse
def create_dim_district():
    postgres_aunt = connect_postgres()
    df = get_data_lake_covid()
    df_dim_district = df[['kode_kab', 'kode_prov', 'nama_kab']]
    df_dim_district = df_dim_district.rename(columns={'kode_kab':'district_id', 'kode_prov':'province_id', 'nama_kab':'district_name' })
    df_dim_district = df_dim_district.drop_duplicates()
    df_dim_district.to_sql(name='dim_district', con=postgres_aunt, index=False, if_exists='replace')
    logging.info("insert data dim_district to dwh postgres success")

# fuction create dimension case table and insert data from data lake to data warehouse
def create_dim_case():
    postgres_aunt = connect_postgres()
    df = get_data_lake_covid()
    column_start = ["suspect_diisolasi", "suspect_discarded", "closecontact_dikarantina", "closecontact_discarded", "probable_diisolasi", "probable_discarded", "confirmation_sembuh", "confirmation_meninggal", "suspect_meninggal", "closecontact_meninggal", "probable_meninggal"]
    column_end = ["id", "status_name", "status_detail", "status"]

    df = df[column_start]
    df = df[:1]
    df = df.melt(var_name="status", value_name='total')
    df = df.drop_duplicates('status').sort_values('status')
    df['id'] = np.arange(1, df.shape[0]+1)
    df[['status_name', 'status_detail']] = df['status'].str.split('_', n=1, expand=True)
    df = df[column_end]

    df.to_sql(name='dim_case', con=postgres_aunt, index=False, if_exists='replace')
    print("insert data dim_Case to dwh postgres success")
    return df

# fuction create fact province daily table and insert data from data lake to data warehouse
def create_fact_table_province_daily():
    postgres_aunt = connect_postgres()
    df = get_data_lake_covid()
    df_dim_case = create_dim_case()
    column_start = ["tanggal", "kode_prov", "suspect_diisolasi", "suspect_discarded", "closecontact_dikarantina", "closecontact_discarded", "probable_diisolasi", "probable_discarded", "confirmation_sembuh", "confirmation_meninggal", "suspect_meninggal", "closecontact_meninggal", "probable_meninggal"]
    column_end = ["date", "province_id", "status", "total"]

    data = df[column_start]
    data = data.melt(id_vars=["tanggal", "kode_prov"], var_name="status", value_name="total").sort_values(["tanggal", "kode_prov", "status"])
    data = data.groupby(by=["tanggal", "kode_prov", "status"]).sum()
    data = data.reset_index()


    data.columns = column_end
    data['id'] = np.arange(1, data.shape[0]+1)
    df_dim_case = df_dim_case.rename({'id':'case_id'}, axis=1)

    data = pd.merge(data, df_dim_case, how='inner', on='status')
    data = data[['id', 'province_id', 'case_id', 'date', 'total']] 

    data.to_sql(name='province_daily', con=postgres_aunt, index=False, if_exists='replace')
    print("insert data province_daily to dwh postgres success")

# fuction create fact district daily table and insert data from data lake to data warehouse
def create_fact_table_district_daily():
    postgres_aunt = connect_postgres()
    df = get_data_lake_covid()
    df_dim_case = create_dim_case()
    column_start = ["tanggal", "kode_kab", "suspect_diisolasi", "suspect_discarded", "closecontact_dikarantina", "closecontact_discarded", "probable_diisolasi", "probable_discarded", "confirmation_sembuh", "confirmation_meninggal", "suspect_meninggal", "closecontact_meninggal", "probable_meninggal"]
    column_end = ["date", "district_id", "status", "total"]

    data = df[column_start]
    data = data.melt(id_vars=["tanggal", "kode_kab"], var_name="status", value_name="total").sort_values(["tanggal", "kode_kab", "status"])
    data = data.groupby(by=["tanggal", "kode_kab", "status"]).sum()
    data = data.reset_index()


    data.columns = column_end
    data['id'] = np.arange(1, data.shape[0]+1)
    df_dim_case = df_dim_case.rename({'id':'case_id'}, axis=1)

    data = pd.merge(data, df_dim_case, how='inner', on='status')
    data = data[['id', 'district_id', 'case_id', 'date', 'total']] 

    data.to_sql(name='district_daily', con=postgres_aunt, index=False, if_exists='replace')
    print("insert data district_daily to dwh postgres success")