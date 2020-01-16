from neuronpp.core.cells.core_cell import CoreCell
from neuronpp.core.hocwrappers.hoc import Hoc


class NetStim(Hoc):
    def __init__(self, hoc_obj, parent: CoreCell, name):
        Hoc.__init__(self, hoc_obj=hoc_obj, parent=parent, name=name)