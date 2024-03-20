import mysql.connector

db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="1990",
        database="webscraperdb"
)

# prepare curso object
CursorObject = db.cursor()

# create database
CursorObject.execute("CREATE DATABASE IF NOT EXISTS webscraperdb")
print("Database created successfully")
