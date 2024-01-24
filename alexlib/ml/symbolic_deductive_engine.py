"""symbolic_deductive_engine.py"""
from alexlib.ml.response import (
    Response,
    symbolic_deductive_engine_path,
)
from alexlib.core import show_dict

sde_response = Response(symbolic_deductive_engine_path)


print(sde_response)

show_dict(sde_response.heading_step_index_map)
show_dict(sde_response.heading_step_map)
