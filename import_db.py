import pymysql

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Ai230592',
    charset='utf8mb4'
)

try:
    with connection.cursor() as cursor:
        print("Creating database...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS caregiver_platform")
        print("Database created")
        
        cursor.execute("USE caregiver_platform")
        
        print("Importing tables...")
        with open('database/db_init.sql', 'r', encoding='utf-8') as f:
            sql_commands = f.read()
            
            for command in sql_commands.split(';'):
                command = command.strip()
                if command:
                    try:
                        cursor.execute(command)
                    except Exception as e:
                        if 'already exists' not in str(e).lower():
                            print(f"Warning: {e}")
        
        connection.commit()
        print("Import complete")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\nTables: {len(tables)}")
        for table in tables:
            print(f"  {table[0]}")
            
finally:
    connection.close()

print("\nDone")
