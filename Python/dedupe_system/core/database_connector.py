# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Database Connectivity Module.

This module implements:
- MySQL database connections
- PostgreSQL database connections
- Query execution for duplicate detection
- Data extraction from databases
- Safe database operations

Supports the optional database connections mentioned in documentation.
"""

import pandas as pd
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import warnings

from .logging_config import get_logger
from .exceptions import DataValidationError

logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    db_type: str  # 'mysql' or 'postgresql'
    host: str
    port: int
    database: str
    username: str
    password: str
    table_name: Optional[str] = None


class DatabaseConnector:
    """
    Handles database connections and data extraction.
    
    Supports MySQL and PostgreSQL databases for duplicate detection
    on database records.
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database connector.
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.connection = None
        self.engine = None
        
        # Check if required libraries are installed
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required database libraries are installed."""
        if self.config.db_type == 'mysql':
            try:
                import pymysql
                self.db_module = pymysql
            except ImportError:
                raise ImportError(
                    "MySQL support requires pymysql. Install with: pip install pymysql"
                )
        elif self.config.db_type == 'postgresql':
            try:
                import psycopg2
                self.db_module = psycopg2
            except ImportError:
                raise ImportError(
                    "PostgreSQL support requires psycopg2. Install with: pip install psycopg2-binary"
                )
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")
    
    def connect(self):
        """
        Establish database connection.
        
        Returns:
            Connection object
        """
        logger.info(f"Connecting to {self.config.db_type} database at {self.config.host}:{self.config.port}")
        
        try:
            if self.config.db_type == 'mysql':
                self.connection = self.db_module.connect(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.username,
                    password=self.config.password,
                    database=self.config.database
                )
            elif self.config.db_type == 'postgresql':
                self.connection = self.db_module.connect(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.username,
                    password=self.config.password,
                    dbname=self.config.database
                )
            
            logger.info("Database connection established")
            return self.connection
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DataValidationError(f"Database connection failed: {e}")
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
            self.connection = None
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            DataFrame with query results
        """
        if not self.connection:
            self.connect()
        
        try:
            logger.debug(f"Executing query: {query}")
            df = pd.read_sql_query(query, self.connection, params=params)
            logger.info(f"Query returned {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DataValidationError(f"Query failed: {e}")
    
    def load_table(self, table_name: Optional[str] = None, 
                   columns: Optional[List[str]] = None,
                   where_clause: Optional[str] = None,
                   limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load data from a database table.
        
        Args:
            table_name: Name of table to load (uses config table_name if None)
            columns: List of columns to select (selects all if None)
            where_clause: Optional WHERE clause
            limit: Optional row limit
            
        Returns:
            DataFrame with table data
        """
        table = table_name or self.config.table_name
        if not table:
            raise ValueError("No table name specified")
        
        # Build query
        col_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {col_str} FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        logger.info(f"Loading data from table: {table}")
        return self.execute_query(query)
    
    def get_table_info(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a table.
        
        Args:
            table_name: Name of table (uses config table_name if None)
            
        Returns:
            Dictionary with table information
        """
        table = table_name or self.config.table_name
        if not table:
            raise ValueError("No table name specified")
        
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            if self.config.db_type == 'mysql':
                # Get column information
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                column_info = [
                    {
                        'name': col[0],
                        'type': col[1],
                        'null': col[2],
                        'key': col[3],
                        'default': col[4]
                    }
                    for col in columns
                ]
                
            elif self.config.db_type == 'postgresql':
                # Get column information
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                """)
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                column_info = [
                    {
                        'name': col[0],
                        'type': col[1],
                        'null': col[2],
                        'default': col[3]
                    }
                    for col in columns
                ]
            
            cursor.close()
            
            return {
                'table_name': table,
                'row_count': row_count,
                'column_count': len(column_info),
                'columns': column_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise DataValidationError(f"Cannot get table info: {e}")
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            if self.config.db_type == 'mysql':
                cursor.execute("SHOW TABLES")
            elif self.config.db_type == 'postgresql':
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            logger.info(f"Found {len(tables)} tables in database")
            return tables
            
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            raise DataValidationError(f"Cannot list tables: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False


# Convenience functions
def load_from_mysql(host: str, database: str, table: str,
                   username: str, password: str,
                   port: int = 3306) -> pd.DataFrame:
    """
    Convenience function to load data from MySQL.
    
    Args:
        host: Database host
        database: Database name
        table: Table name
        username: Database username
        password: Database password
        port: Database port (default: 3306)
        
    Returns:
        DataFrame with table data
    """
    config = DatabaseConfig(
        db_type='mysql',
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        table_name=table
    )
    
    with DatabaseConnector(config) as conn:
        return conn.load_table()


def load_from_postgresql(host: str, database: str, table: str,
                        username: str, password: str,
                        port: int = 5432) -> pd.DataFrame:
    """
    Convenience function to load data from PostgreSQL.
    
    Args:
        host: Database host
        database: Database name
        table: Table name
        username: Database username
        password: Database password
        port: Database port (default: 5432)
        
    Returns:
        DataFrame with table data
    """
    config = DatabaseConfig(
        db_type='postgresql',
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        table_name=table
    )
    
    with DatabaseConnector(config) as conn:
        return conn.load_table()
