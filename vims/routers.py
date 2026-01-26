"""
Database routers for read/write splitting.
Routes read queries to read replicas for better performance.
"""
import random


class ReadReplicaRouter:
    """
    Database router for read/write split.
    - All writes go to 'default' (primary DB)
    - 90% of reads go to read replicas
    - 10% of reads go to primary (for freshness)
    """
    
    def db_for_read(self, model, **hints):
        """
        Route read operations to read replicas.
        """
        # Check if read replicas are configured
        from django.conf import settings
        
        replicas = [
            db for db in settings.DATABASES.keys()
            if db.startswith('read_replica')
        ]
        
        if replicas:
            # 10% chance to read from primary for data freshness
            if random.random() < 0.1:
                return 'default'
            # 90% to read replicas
            return random.choice(replicas)
        
        # If no replicas configured, use default
        return 'default'
    
    def db_for_write(self, model, **hints):
        """
        All writes go to the primary database.
        """
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects in the same database.
        """
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All migrations run on the primary database only.
        """
        return db == 'default'





