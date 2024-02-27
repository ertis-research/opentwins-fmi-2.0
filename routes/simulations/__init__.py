from fastapi import APIRouter
from routes.simulations.simulation_id import simulation_id


simulations = APIRouter(prefix='/simulations', tags=['simulations'])
simulations.include_router(simulation_id)

@simulations.get('')
async def get_simulation_list():
    return "Lista de simulaciones"

@simulations.post('')
async def get_simulation_list2():
    return "Creada simulacion"
    # try:
    #     data = fmu_list(context)
    #     return data
    # except FileNotFoundError:
    #     abort(400)
