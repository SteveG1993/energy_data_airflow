"""
DAG to fetch hourly LMP (Locational Marginal Pricing) data from ISO New England API.

This DAG fetches day-ahead final hourly LMP data from ISO-NE and stores it in a SQLite database.
Runs hourly to capture the latest available data.
"""

from datetime import datetime, timedelta
import sqlite3
import json
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.http.hooks.http import HttpHook


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


def fetch_iso_ne_data(**context):
    """
    Fetch hourly LMP data from ISO-NE API using HTTP Basic Authentication.
    """
    # Get the HTTP connection
    http_hook = HttpHook(http_conn_id='iso_ne_api', method='GET')

    # Use 'latest' to get the most recent available data
    # API endpoint - using /day/latest to get the latest available data
    endpoint = '/api/v1.1/hourlylmp/da/final/day/latest.json'

    # Set headers to request JSON response
    headers = {
        'Accept': 'application/json'
    }

    print(f"Requesting latest available data")
    print(f"Endpoint: {endpoint}")

    try:
        # Make the API request with headers (no data/params needed, date is in URL)
        response = http_hook.run(endpoint, headers=headers)

        # Check if we got a valid response
        print(f"Response status code: {response.status_code}")
        print(f"Response content length: {len(response.content)}")

        # Parse JSON response
        if response.content:
            data = response.json()
        else:
            print("Warning: Empty response from API")
            print(f"Response headers: {response.headers}")
            raise ValueError("Empty response from ISO-NE API")

        # Log summary
        if 'HourlyLmps' in data and 'HourlyLmp' in data['HourlyLmps']:
            records = data['HourlyLmps']['HourlyLmp']
            print(f"Successfully fetched {len(records)} LMP records from ISO-NE API")
        else:
            print(f"API response structure: {list(data.keys())}")
            records = []

        # Push data to XCom for next task
        context['task_instance'].xcom_push(key='lmp_data', value=data)

        return data

    except Exception as e:
        print(f"Error fetching data from ISO-NE API: {str(e)}")
        print(f"Response text (first 500 chars): {response.text[:500] if hasattr(response, 'text') else 'N/A'}")
        raise


def save_to_database(**context):
    """
    Save the fetched LMP data to SQLite database.
    """
    # Pull data from previous task
    data = context['task_instance'].xcom_pull(task_ids='fetch_lmp_data', key='lmp_data')

    if not data:
        print("No data to save")
        return

    # Database path
    db_path = '/Users/stevengregoire/airflow/energy_data.db'

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hourly_lmp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id TEXT,
                location_name TEXT,
                location_type TEXT,
                begin_date TEXT,
                hour_ending TEXT,
                lmp_total REAL,
                energy_component REAL,
                congestion_component REAL,
                loss_component REAL,
                fetched_at TEXT,
                UNIQUE(location_id, begin_date, hour_ending)
            )
        ''')

        # Parse and insert data
        records_inserted = 0
        records_updated = 0

        if 'HourlyLmps' in data and 'HourlyLmp' in data['HourlyLmps']:
            lmp_records = data['HourlyLmps']['HourlyLmp']

            # Handle both single record (dict) and multiple records (list)
            if isinstance(lmp_records, dict):
                lmp_records = [lmp_records]

            for record in lmp_records:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO hourly_lmp
                        (location_id, location_name, location_type, begin_date, hour_ending,
                         lmp_total, energy_component, congestion_component, loss_component, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record.get('LocationId'),
                        record.get('LocationName'),
                        record.get('LocationType'),
                        record.get('BeginDate'),
                        record.get('BeginDateHour'),
                        record.get('LmpTotal'),
                        record.get('EnergyComponent'),
                        record.get('CongestionComponent'),
                        record.get('LossComponent'),
                        datetime.now().isoformat()
                    ))

                    if cursor.rowcount > 0:
                        records_inserted += 1

                except Exception as e:
                    print(f"Error inserting record: {str(e)}")
                    continue

        conn.commit()
        print(f"Successfully saved {records_inserted} records to database")
        print(f"Database location: {db_path}")

        # Query and display summary
        cursor.execute('SELECT COUNT(*) FROM hourly_lmp')
        total_records = cursor.fetchone()[0]
        print(f"Total records in database: {total_records}")

    except Exception as e:
        print(f"Error saving to database: {str(e)}")
        conn.rollback()
        raise

    finally:
        conn.close()


# Define the DAG
with DAG(
    dag_id='iso_ne_hourly_lmp',
    default_args=default_args,
    description='Fetch hourly LMP data from ISO New England API',
    schedule='@hourly',  # Run every hour (Airflow 3.x uses 'schedule' instead of 'schedule_interval')
    catchup=False,  # Don't backfill historical runs
    tags=['energy', 'iso-ne', 'lmp', 'api'],
) as dag:

    # Task 1: Fetch data from API
    fetch_lmp_data = PythonOperator(
        task_id='fetch_lmp_data',
        python_callable=fetch_iso_ne_data,
    )

    # Task 2: Save data to database
    save_to_db = PythonOperator(
        task_id='save_to_database',
        python_callable=save_to_database,
    )

    # Define task dependencies
    fetch_lmp_data >> save_to_db
