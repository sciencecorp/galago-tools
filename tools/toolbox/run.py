from tools.toolbox.db import Db
from typing import Any, Dict, List, Optional, Union

db = Db()

class RunError(Exception):
    """Base class for Run related errors."""
    pass

class ProtocolNotFoundError(RunError):
    """Error raised when a protocol is not found."""
    pass

class ProtocolGenerationFailedError(RunError):
    """Error raised when commands cannot be generated for a protocol."""
    pass

class ProtocolParamsInvalidError(RunError):
    """Error raised when protocol parameters are invalid."""
    def __init__(self, message: str, cause: Any = None) -> None:
        super().__init__(message)
        self.cause = cause

class RunStore:
    """Store for managing runs."""
    
    def __init__(self) -> None:
        """Initialize the run store."""
        self._runs = {}
    
    def all(self) -> List[Dict[str, Any]]:
        """Get all runs."""
        # This would typically query the database, but for now we use the in-memory store
        return list(self._runs.values())
    
    def get(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a run by ID."""
        # This would typically query the database, but for now we use the in-memory store
        return self._runs.get(run_id)
    
    async def createFromProtocol(self, workcell_name: str, protocol_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new run from a protocol."""
        # In a real implementation, this would:
        # 1. Get the protocol
        # 2. Validate the params
        # 3. Generate commands
        # 4. Create and store the run
        # For now, we'll simulate this process
        
        # Check if protocol exists
        protocol = db.get_by_id_or_name(protocol_id, "protocols")
        if not protocol:
            raise ProtocolNotFoundError(f"Protocol {protocol_id} not found")
        
        # Here we would validate params and generate commands
        # For now, we'll create a simple run object
        import uuid
        run_id = str(uuid.uuid4())
        run = {
            "id": run_id,
            "workcell_name": workcell_name,
            "protocol_id": protocol_id,
            "params": params,
            "status": "created",
            "created_at": "now",  # Would be a timestamp
        }
        
        # Store the run
        self._runs[run_id] = run
        
        return run

# Create a global instance of RunStore
global_store = RunStore()

def get_all_runs() -> List[Dict[str, Any]]:
    """Get all runs."""
    return global_store.all()

def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Get a run by ID."""
    return global_store.get(run_id)

async def create_run(workcell_name: str, protocol_id: str, params: Dict[str, Any], number_of_runs: Optional[int] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Create one or more runs from a protocol."""
    if number_of_runs and number_of_runs > 1:
        runs = []
        for _ in range(number_of_runs):
            run = await global_store.createFromProtocol(workcell_name, protocol_id, params)
            runs.append(run)
        return runs
    else:
        return await global_store.createFromProtocol(workcell_name, protocol_id, params)
