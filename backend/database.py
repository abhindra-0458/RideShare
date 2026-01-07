import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from config import DATABASE
from logger import logger, error as log_error

class Database:
    def __init__(self):
        self.pool = None
        self.connection_string = None

    def initialize(self):
        try:
            # Build connection string
            self.connection_string = (
                f"dbname={DATABASE['name']} "
                f"user={DATABASE['user']} "
                f"password={DATABASE['password']} "
                f"host={DATABASE['host']} "
                f"port={DATABASE['port']}"
            )
            
            # Test connection
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute('SELECT NOW()')
            cursor.close()
            conn.close()
            
            logger.info('✅ Database connected')
        except Exception as error:
            log_error(f'❌ Database connection error: {str(error)}')
            raise

    def query(self, text, params=None):
        """Execute a query and return results"""
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(text, params or ())
            
            # Check if SELECT query
            if text.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
            
            cursor.close()
            conn.close()
            return result
        except Exception as error:
            log_error(f'Database query error: {str(error)}')
            raise

    async def query_async(self, text, params=None):
        """Async wrapper for query"""
        return self.query(text, params)

# Singleton instance
database = Database()
