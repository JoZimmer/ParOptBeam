from source.postprocess.skin_model.Visualiser import Visualiser
from source.postprocess.skin_model.LineStructureModel import LineStructure
from source.postprocess.skin_model.StructureModel import Structure


def visualize_skin_model(skin_model_params):
    s = Structure(skin_model_params)
    ls = LineStructure(skin_model_params)
    plotter = Visualiser(ls, s)

