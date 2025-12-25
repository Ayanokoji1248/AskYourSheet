from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from io import BytesIO
import os, re
from datetime import datetime


app = FastAPI()

def clean_columns(columns):
    cleaned = []
    for col in columns:
        col = str(col).strip().lower().replace(" ", "_")
        col = "".join(c for c in col if c.isalnum() or c == "_")
        cleaned.append(col)
    return cleaned

def clean_table_name(filename: str) -> str:
    
    name = os.path.splitext(filename)[0]
    name = name.strip().lower().replace(" ", "_")
    name = re.sub(r"[^a-z0-9_]", "", name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{name}_{timestamp}"

@app.post("/analyze")
async def analyze_excel(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content))

        if df.empty:
            raise HTTPException(status_code=400, detail="Excel file is empty")

        # clean column names
        df.columns = clean_columns(df.columns)

        # 👇 table name from file name
        table_name = clean_table_name(file.filename)

        conn = psycopg2.connect(
            dbname="askyoursheet",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        create_sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {",".join([f'"{c}" TEXT' for c in df.columns])}
        )
        '''
        cursor.execute(create_sql)

        insert_sql = f'''
        INSERT INTO "{table_name}" ({",".join([f'"{c}"' for c in df.columns])})
        VALUES %s
        '''
        execute_values(cursor, insert_sql, df.values.tolist())
        conn.commit()

        return {
            "table_created": table_name,
            "rows_inserted": len(df),
            "columns": df.columns.tolist()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
