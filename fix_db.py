import psycopg2
import os

# Database connection details
DATABASE_URL = "postgresql://cleaning_validation_db_user:Rvy2FS9PK54pacbayVMSTB8CXlDfXrb8@dpg-d81eh5dckfvc738c379g-a.oregon-postgres.render.com/cleaning_validation_db"

try:
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("📝 Adding missing columns to products table...")
    
    sqls = [
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS product_code VARCHAR;",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS toxicity_class INTEGER DEFAULT 3;",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS potency_class INTEGER DEFAULT 3;",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS cleanability_rating INTEGER DEFAULT 2;",
        "UPDATE products SET product_code = UPPER(SUBSTRING(name, 1, 6)) WHERE product_code IS NULL;",
        "SELECT COUNT(*) as total_products, COUNT(product_code) as products_with_code FROM products;"
    ]
    
    for sql in sqls:
        cursor.execute(sql)
        if sql.startswith("SELECT"):
            result = cursor.fetchone()
            print(f"   ✅ {result[0]} total products, {result[1]} have product_code")
        else:
            print(f"   ✅ Executed: {sql[:60]}...")
    
    cursor.close()
    conn.close()
    print("\n🎉 Database columns added successfully!")
    print("   Now products endpoint should work.")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure you have installed: pip install psycopg2-binary")
