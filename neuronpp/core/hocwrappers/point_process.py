from neuronpp.core.cells.core_cell import CoreCell
from neuronpp.core.hocwrappers.hoc_wrapper import HocWrapper


class PointProcess(HocWrapper):
    def __init__(self, hoc_obj, name, parent: CoreCell, mod_name):
        HocWrapper.__init__(self, hoc_obj=hoc_obj, parent=parent, name=name)
        self.mod_name = mod_name

    def __repr__(self):
        return "{}+{}+{}+{}".format(self.parent, self.__class__.__name__, self.mod_name, self.name)
