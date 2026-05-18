import psycopg2
import bcrypt

# Database connection
conn = psycopg2.connect('postgresql://cleaning_validation_db_user:Rvy2FS9PK54pacbayVMSTB8CXlDfXrb8@dpg-d81eh5dckfvc738c379g-a.oregon-postgres.render.com/cleaning_validation_db')
conn.autocommit = True
cur = conn.cursor()

# Hash password 'admin'
hashed = bcrypt.hashpw('admin'.encode(), bcrypt.gensalt()).decode()

# Update admin password
cur.execute("UPDATE users SET hashed_password = %s WHERE username = 'admin'", (hashed,))

print('✅ Admin password reset to: admin')
conn.close()
