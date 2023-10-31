import psycopg2

config = psycopg2.connect(
    host='host', 
    database='database',
    user='user',    
    password='password'
)

current = config.cursor()
sql = '''
    CREATE TABLE barber (
        id BIGINT,
        name VARCHAR(255),
        date DATE,
        time TIME,
        phonenumber CHAR(11)
    );
''' 

current.execute(sql)

current.close()
config.commit()
config.close()