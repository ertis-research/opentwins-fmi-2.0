class FMIError(Exception):
    pass


class FMUError(FMIError):
    pass


class SimulationError(Exception):
    pass
class DeleteSimulationError(SimulationError):
    pass
class SimulationAlreadyExistsError(SimulationError):
    pass

class DatabaseError(Exception):
    pass

class SchemaNotFoundError(DatabaseError):
    pass