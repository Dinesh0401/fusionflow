"""Backend adapters for different execution engines"""

class BackendAdapter:
    """Base class for backend adapters"""
    
    def can_execute(self, operation):
        """Check if this backend can execute the operation"""
        raise NotImplementedError
    
    def execute(self, operation, data):
        """Execute operation on data"""
        raise NotImplementedError

class PandasBackend(BackendAdapter):
    """Pandas execution backend"""
    
    def can_execute(self, operation):
        return operation in ['filter', 'transform', 'join', 'aggregate']
    
    def execute(self, operation, data):
        # Pandas execution logic
        return data

class SparkBackend(BackendAdapter):
    """Spark execution backend (future)"""
    
    def can_execute(self, operation):
        return False  # Not implemented yet
    
    def execute(self, operation, data):
        raise NotImplementedError("Spark backend not implemented")
