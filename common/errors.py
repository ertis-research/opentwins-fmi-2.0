class FMUError(Exception):
    pass

class SimulationError(Exception):
    pass

class MQTTInputError(SimulationError):
    pass
