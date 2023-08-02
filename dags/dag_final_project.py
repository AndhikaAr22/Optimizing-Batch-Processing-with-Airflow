from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from package.insert_data_db import insert_raw_data, create_dim_case, create_dim_district, create_dim_province, create_fact_table_district_daily, create_fact_table_province_daily
import logging

def generate_dim():
    create_dim_province()
    create_dim_district()
    create_dim_case()
    logging.info("success insert data to dimention table")

def create_fact_district_daily():
    create_fact_table_district_daily()
    logging.info("success insert data to fact table")

def create_fact_province_daily():
    create_fact_table_province_daily()
    logging.info("success insert data to fact table")


with DAG(
    dag_id='dag_final_project_digitalskola',
    start_date=datetime(2023, 6, 23),
    schedule_interval='0 0 * * *',
    catchup=False
) as dag:
    get_data_from_api = PythonOperator(
        task_id = 'get_data_from_api',
        python_callable = insert_raw_data
    )

    generate_dim_table = PythonOperator(
        task_id = 'generate_dim',
        python_callable = generate_dim
    )

    insert_district_daily = PythonOperator(
        task_id = 'insert_district_daily',
        python_callable = create_fact_district_daily
    )

    insert_province_daily = PythonOperator(
        task_id = 'insert_province_daily',
        python_callable = create_fact_province_daily
    )

    get_data_from_api >> generate_dim_table 
    generate_dim_table >> insert_district_daily
    generate_dim_table >> insert_province_daily