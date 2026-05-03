# Function for mysql database connection
import mysql.connector
import yaml

def get_db_connection():
    with open("app_conf.yaml", 'r') as f:
        config = yaml.safe_load(f)

    db = config["database"]
    return mysql.connector.connect(
        host=db["hostname"],
        user=db["user"],
        password=db["password"],
        database=db["db"]
    )