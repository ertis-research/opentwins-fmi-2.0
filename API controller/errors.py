class FMIError(Exception):
    pass


class FMUError(FMIError):
    pass


class SimulationError(FMIError):
    pass


class DatabaseError(Exception):
    pass

class SchemaNotFoundError(DatabaseError):
    pass