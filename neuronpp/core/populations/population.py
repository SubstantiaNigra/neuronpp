import abc
import numpy as np
from neuronpp.core.hocwrappers.sec import Sec

from neuronpp.core.cells.core_cell import CoreCell

from neuronpp.cells.cell import Cell
from neuronpp.utils.record import Record


class Population:
    def __init__(self, name):
        self.name = name
        self.cell_counter = 0
        self.cells = []
        self.syns = []
        self.recs = {}

    def create(self, cell_num, **kwargs):
        result = []
        for i in range(cell_num):
            cell = self.make_cell(**kwargs)
            self.cell_counter += 1
            self.cells.append(cell)
            result.append(cell)

        return result

    def add_mechs(self, single_cell_mechs):
        for cell in self.cells:
            single_cell_mechs(cell)

    def connect(self, source, source_sec_name="soma", source_loc=0.5, rule="all", **kwargs):
        """
        :param source:
            None for empty sources, int for empty source int-times, NetStim/VecStim, Cell/s, CoreCell/s
            or other Population for connections.
            If it is Cell/s, CoreCell/s or Population consider to change 'source_sec_name' and 'source_loc' params.
        :param source_sec_name:
            Default None. If source is None, VecStim/NetStim or int - it will not be used.
        :param source_loc:
            Default None. If source is None, VecStim/NetStim or int - it will not be used.
        :param rule:
            'all' - all-to-all connections
            'one' - one-to-one connections
        :return:
            list of list of synapses
        """
        result = []
        if source is None:
            source = [None for _ in range(len(self.cells))]

        elif isinstance(source, int):
            source = [None for _ in range(source)]

        elif isinstance(source, Population):
            source = source.cells

        elif not isinstance(source, (list, set, np.ndarray)):
            source = [source]

        if isinstance(source[0], Sec):
            raise TypeError("If you want to connect other Cell/s you must provide Cell object, not its sections.")

        if isinstance(source[0], CoreCell):
            if (source_sec_name is None or source_loc is None):
                raise ValueError("If source is type of Cell, CoreCell or Population you must provide "
                                 "'source_sec_name' and 'source_loc' params.")

            source = [cell.filter_secs(source_sec_name)[0] for cell in source]

        if rule == 'all':
            for source in source:
                for cell in self.cells:
                    syns = self.make_conn(cell=cell, source=source, source_loc=source_loc, **kwargs)
                    result.append(syns)

        elif rule == 'one':
            if len(source) != len(self.cells):
                raise LookupError("for rule 'one' len of sources and population cells must be the same, "
                                  "but it was %s and %s respectively." % (len(source), len(self.cells)))

            for source, cell in zip(source, self.cells):
                syns = self.make_conn(cell=cell, source=source, source_loc=source_loc, **kwargs)
                result.append(syns)
        else:
            raise TypeError("The only allowed rules are 'all' or 'one', but provided rule '%s'" % rule)

        self.syns.extend(result)
        return result

    def record(self, sec_name="soma", loc=0.5, variable='v'):
        d = [cell.filter_secs(sec_name)[0] for cell in self.cells]
        rec = Record(d, loc=loc, variables=variable)
        self.recs[variable] = rec

    def plot(self, animate=False, **kwargs):
        """
        Plots each recorded variable for each neurons in the population.

        If animate=True it will live update graphs. Other params are for live update purpose.

        :param animate:
            If True it will live update graphs.
        :param steps:
            how many timesteps to see on the graph
        :param y_lim:
            tuple of limits for y axis. Default is (-80, 50)
        :param position:
            position of all subplots ON EACH figure (each figure is created for each variable separately).
            * position=(3,3) -> if you have 9 neurons and want to display 'v' on 3x3 matrix
            * position='merge' -> it will display all figures on the same graph.
            * position=None -> Default, each neuron has separated  axis (row) on the figure.
        """
        for r in self.recs.values():
            r.plot(animate=animate, **kwargs)

    @abc.abstractmethod
    def make_conn(self, cell: Cell, source, source_loc=None, **kwargs) -> list:
        """
        Must return syns list.
        :param cell:
        :param source:
            list of Secs
        :return:
            Must return a list of synapses.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def make_cell(self, **kwargs) -> Cell:
        """
        You can pass any param you like to this this method
        as long as you provide default param during the method definition.
        :return:
            Must return a single cell created by the population.
        """
        raise NotImplementedError()
