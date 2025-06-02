
import os
import psycopg2
import json
import logging
from datetime import datetime
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database operations for misinformation tracking"""
    
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            logger.warning("DATABASE_URL not found - database features disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.init_tables()
    
    def get_connection(self):
        """Get database connection"""
        if not self.enabled:
            return None
        return psycopg2.connect(self.database_url)
    
    def init_tables(self):
        """Initialize database tables if they don't exist"""
        if not self.enabled:
            return
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Create fact_entries table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fact_entries (
                    id SERIAL PRIMARY KEY,
                    claim TEXT NOT NULL,
                    fact_check TEXT NOT NULL,
                    sources TEXT,
                    truthiness_score INTEGER,
                    category VARCHAR(100),
                    tags TEXT,
                    added_by_user_id BIGINT,
                    guild_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create misinformation_patterns table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS misinformation_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_text TEXT NOT NULL,
                    description TEXT,
                    severity VARCHAR(20) DEFAULT 'medium',
                    frequency INTEGER DEFAULT 1,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    guild_id BIGINT,
                    added_by_user_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create trusted_sources table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trusted_sources (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    url TEXT NOT NULL,
                    description TEXT,
                    credibility_score INTEGER DEFAULT 90,
                    category VARCHAR(100),
                    added_by_user_id BIGINT,
                    guild_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database tables: {e}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    def add_fact_entry(self, claim, fact_check, sources=None, truthiness_score=None, 
                      category=None, tags=None, user_id=None, guild_id=None):
        """Add a fact-check entry to the database"""
        if not self.enabled:
            return False
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO fact_entries 
                (claim, fact_check, sources, truthiness_score, category, tags, added_by_user_id, guild_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (claim, fact_check, sources, truthiness_score, category, tags, user_id, guild_id))
            
            entry_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Added fact entry with ID {entry_id}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Error adding fact entry: {e}")
            return False
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    def add_misinformation_pattern(self, pattern_text, description=None, severity='medium', 
                                 user_id=None, guild_id=None):
        """Add a misinformation pattern to track"""
        if not self.enabled:
            return False
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Check if pattern already exists for this guild
            cur.execute("""
                SELECT id, frequency FROM misinformation_patterns 
                WHERE pattern_text = %s AND guild_id = %s
            """, (pattern_text, guild_id))
            
            existing = cur.fetchone()
            
            if existing:
                # Update frequency and last_seen
                cur.execute("""
                    UPDATE misinformation_patterns 
                    SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (existing[0],))
                pattern_id = existing[0]
            else:
                # Insert new pattern
                cur.execute("""
                    INSERT INTO misinformation_patterns 
                    (pattern_text, description, severity, added_by_user_id, guild_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (pattern_text, description, severity, user_id, guild_id))
                pattern_id = cur.fetchone()[0]
            
            conn.commit()
            logger.info(f"Added/updated misinformation pattern with ID {pattern_id}")
            return pattern_id
            
        except Exception as e:
            logger.error(f"Error adding misinformation pattern: {e}")
            return False
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    def add_trusted_source(self, name, url, description=None, credibility_score=90, 
                          category=None, user_id=None, guild_id=None):
        """Add a trusted source to the database"""
        if not self.enabled:
            return False
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO trusted_sources 
                (name, url, description, credibility_score, category, added_by_user_id, guild_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (name, url, description, credibility_score, category, user_id, guild_id))
            
            source_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Added trusted source with ID {source_id}")
            return source_id
            
        except Exception as e:
            logger.error(f"Error adding trusted source: {e}")
            return False
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    def search_fact_entries(self, query, guild_id=None, limit=10):
        """Search fact entries by claim text"""
        if not self.enabled:
            return []
        
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            search_query = f"%{query}%"
            if guild_id:
                cur.execute("""
                    SELECT * FROM fact_entries 
                    WHERE (claim ILIKE %s OR fact_check ILIKE %s) AND guild_id = %s
                    ORDER BY created_at DESC LIMIT %s
                """, (search_query, search_query, guild_id, limit))
            else:
                cur.execute("""
                    SELECT * FROM fact_entries 
                    WHERE claim ILIKE %s OR fact_check ILIKE %s
                    ORDER BY created_at DESC LIMIT %s
                """, (search_query, search_query, limit))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error searching fact entries: {e}")
            return []
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    def get_misinformation_patterns(self, guild_id=None, limit=20):
        """Get misinformation patterns, optionally filtered by guild"""
        if not self.enabled:
            return []
        
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            if guild_id:
                cur.execute("""
                    SELECT * FROM misinformation_patterns 
                    WHERE guild_id = %s
                    ORDER BY frequency DESC, last_seen DESC LIMIT %s
                """, (guild_id, limit))
            else:
                cur.execute("""
                    SELECT * FROM misinformation_patterns 
                    ORDER BY frequency DESC, last_seen DESC LIMIT %s
                """, (limit,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting misinformation patterns: {e}")
            return []
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
