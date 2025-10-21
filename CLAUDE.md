# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Apache Airflow 3.1.0 installation configured for local development and workflow orchestration. The setup uses a Python virtual environment and runs in standalone mode with a SQLite backend.

## Environment Setup

### Virtual Environment
All Airflow commands must be run within the virtual environment:
```bash
source ~/airflow_venv/bin/activate
```

Alternatively, use the provided startup script:
```bash
./run_first.sh
```

### Airflow Home
- **AIRFLOW_HOME**: `/Users/stevengregoire/airflow`
- **DAGs folder**: `/Users/stevengregoire/airflow/dags`
- **Database**: SQLite at `/Users/stevengregoire/airflow/airflow.db`
- **Configuration**: `airflow.cfg` in the root directory

## Common Commands

### Starting Airflow
```bash
# Activate virtual environment first
source ~/airflow_venv/bin/activate

# Start Airflow standalone (includes webserver and scheduler)
airflow standalone

# Or start components separately:
airflow scheduler    # Start scheduler
airflow webserver    # Start web UI (default port 8080)
```

### DAG Management
```bash
# List all DAGs
airflow dags list

# Test a specific DAG
airflow dags test <dag_id> <execution_date>

# Trigger a DAG run
airflow dags trigger <dag_id>

# Pause/unpause a DAG
airflow dags pause <dag_id>
airflow dags unpause <dag_id>

# Show DAG structure
airflow dags show <dag_id>

# Check for import errors
airflow dags list-import-errors
```

### Task Operations
```bash
# List tasks for a DAG
airflow tasks list <dag_id>

# Test a specific task (doesn't save state)
airflow tasks test <dag_id> <task_id> <execution_date>

# Run a task instance
airflow tasks run <dag_id> <task_id> <execution_date>

# Clear task instances
airflow tasks clear <dag_id>
```

### Debugging and Development
```bash
# Check Airflow configuration
airflow config list
airflow config get-value <section> <key>

# View system information
airflow info

# Check loaded plugins
airflow plugins

# View Airflow version
airflow version
```

## Configuration Details

### Executor
- **Type**: LocalExecutor
- **Parallelism**: 32 concurrent tasks
- Suitable for local development and small-scale deployments

### Authentication
- **Auth Manager**: SimpleAuthManager
- **Default User**: `admin:admin`
- **Mode**: Authentication enabled (not all_admins mode)
- **Password file**: `AIRFLOW_HOME/simple_auth_manager_passwords.json.generated`

### Database
- **Backend**: SQLite
- **Location**: `airflow.db` in AIRFLOW_HOME
- **Note**: SQLite is not suitable for production; consider PostgreSQL or MySQL for multi-node deployments

## DAG Development

### DAG Location
All DAGs must be placed in: `/Users/stevengregoire/airflow/dags/`

### DAG Structure (Reference: first_dag.py)
The test DAG demonstrates best practices:
- Import required operators (PythonOperator, BashOperator, DummyOperator)
- Define `default_args` with owner, start_date, retries, etc.
- Use `days_ago()` for start dates in development
- Set `catchup=False` to avoid backfilling
- Use tags for organization
- Leverage XCom for task data passing
- Define task dependencies using `>>` operator

### Task Types Used
- **PythonOperator**: Execute Python functions
- **BashOperator**: Execute bash commands
- **DummyOperator**: Placeholder/organizational tasks

### XCom Usage
Tasks can pass data between each other:
```python
# Push data
context['task_instance'].xcom_push(key='data_key', value=data)

# Pull data
data = context['task_instance'].xcom_pull(task_ids='source_task', key='data_key')
```

## Project Structure

```
/Users/stevengregoire/airflow/
├── airflow.cfg              # Main configuration file
├── airflow.db               # SQLite database
├── dags/                    # DAG definitions directory
│   └── first_dag.py        # Example test DAG
├── logs/                    # Task execution logs
├── run_first.sh            # Environment activation script
└── notes.txt               # Project notes
```

## Development Workflow

1. **Activate the virtual environment**: `source ~/airflow_venv/bin/activate`
2. **Create or modify DAGs**: Add Python files to `dags/` directory
3. **Test DAG imports**: `airflow dags list-import-errors`
4. **Test individual tasks**: `airflow tasks test <dag_id> <task_id> <date>`
5. **Start Airflow services**: `airflow standalone` or start scheduler/webserver separately
6. **Access Web UI**: Navigate to `http://localhost:8080`
7. **Monitor logs**: Check `logs/` directory for task execution details

## Important Notes

- Always activate the virtual environment before running Airflow commands
- DAG files are scanned every few seconds; changes are auto-detected
- Use `schedule_interval=None` for manually triggered DAGs
- Set `provide_context=True` for PythonOperators that need access to Airflow context
- The SQLite backend does not support parallel writes; use LocalExecutor with caution
- Example DAGs are enabled (`load_examples = True` in config)
