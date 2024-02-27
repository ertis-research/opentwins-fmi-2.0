
from fastapi import APIRouter

simulation_id = APIRouter(prefix='/{simulation_id}', tags=['simulation_id'])

@simulation_id.get('')
async def get_simulation_list():
    return ["Simulacion guapisima"]

@simulation_id.delete('')
async def get_simulation_list2():
    return ["Borrada simulacion guapisima"]
    # try:
    #     data = fmu_list(context)
    #     return data
    # except FileNotFoundError:
    #     abort(400)
@simulation_id.patch('/pause')
async def pause_simulation():
    return ["Simulacion pausada"]

@simulation_id.patch('/resume')
async def resume_simulation():
    return ["Simulacion reanudada"] 
