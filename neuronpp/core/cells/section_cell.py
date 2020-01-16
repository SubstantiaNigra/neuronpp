from os import path

from neuron import h

from neuronpp.core.cells.cell import Cell
from neuronpp.core.wrappers.sec import Sec

h.load_file('stdlib.hoc')
h.load_file('import3d.hoc')


class SectionCell(Cell):
    def __init__(self, name):
        """
        :param name:
            Name of the cell
        """
        Cell.__init__(self, name)
        # if Cell (named core_cell) have been built before on the stack of super() objects
        if not hasattr(self, '_core_cell_builded'):
            self.secs = []
            self._core_cell_builded = True

    def filter_secs(self, name):
        """
        :param name:
            start with 'regex:any pattern' to use regular expression. If without 'regex:' - will look which Hoc objects contain the str
        :return:
        """
        return self.filter(searchable=self.secs, name=name)

    def insert(self, mechanism_name: str, sec=None):
        if isinstance(sec, str) or sec is None:
            sec = self.filter_secs(name=sec)
        for s in sec:
            s.hoc.insert(mechanism_name)

    def make_sec(self, name: str, diam=None, l=None, nseg=1):
        """
        :param name:
        :param diam:
        :param l:
        :param nseg:
        :return:
        """
        hoc_sec = h.Section(name=name, cell=self)
        hoc_sec.L = l
        hoc_sec.diam = diam
        hoc_sec.nseg = nseg

        sec = Sec(hoc_sec, parent=self, name=name)
        self.secs.append(sec)
        return sec

    def connect_secs(self, source, target, source_loc=1.0, target_loc=0.0):
        """
        default: source(0.0) -> target(1.0)
        :param source:
        :param target:
        :param source_loc:
        :param target_loc:
        :return:
        """
        if source is None or target is None:
            raise LookupError("source and target must be specified. Can't be None.")

        if isinstance(source, str):
            source = self.filter_secs(name=source)
            if len(source) != 1:
                raise LookupError("To connect sections source name must return exactly 1 Section, "
                                  "but returned %s elements for name=%s" % (len(source), source))
            source = source[0]

        if isinstance(target, str) or target is None:
            target = self.filter_secs(name=target)
            if len(target) != 1:
                raise LookupError("To connect sections target name must return exactly 1 Section, "
                                  "but returned %s elements for name=%s" % (len(source), source))
            target = target[0]

        target_loc = float(target_loc)
        source_loc = float(source_loc)

        source.hoc.connect(target.hoc(source_loc), target_loc)

    def load_morpho(self, filepath, seg_per_L_um=1.0, make_const_segs=11):
        """
        :param filepath:
            swc file path
        :param seg_per_L_um:
            how many segments per single um of L, Length.  Can be < 1. None is 0.
        :param make_const_segs:
            how many segments have each section by default.
            With each um of L this number will be increased by seg_per_L_um
        """
        if not path.exists(filepath):
            raise FileNotFoundError(filepath)

        # SWC
        fileformat = filepath.split('.')[-1]
        if fileformat == 'swc':
            morpho = h.Import3d_SWC_read()
        # Neurolucida
        elif fileformat == 'asc':
            morpho = h.Import3d_Neurolucida3()
        else:
            raise Exception('file format `%s` not recognized' % filepath)

        self.all = []
        morpho.input(filepath)
        h.Import3d_GUI(morpho, 0)
        i3d = h.Import3d_GUI(morpho, 0)
        i3d.instantiate(self)

        # add all SWC sections to self.secs; self.all is defined by SWC import
        for hoc_sec in self.all:
            # change segment number based on seg_per_L_um and make_const_segs
            add = int(hoc_sec.L * seg_per_L_um) if seg_per_L_um is not None else 0
            hoc_sec.nseg = make_const_segs + add

            name = hoc_sec.name().split('.')[-1]  # eg. name="dend[19]"

            sec = Sec(hoc_sec, parent=self, name=name)
            self.secs.append(sec)

        del self.all

    def set_cell_position(self, x, y, z):
        h.define_shape()
        for sec in self.secs:
            for i in range(sec.n3d()):
                sec.pt3dchange(i,
                               x - sec.x3d(i),
                               y - sec.y3d(i),
                               z - sec.z3d(i),
                               sec.diam3d(i))

    def rotate_cell_z(self, theta):
        h.define_shape()
        """Rotate the cell about the Z axis."""
        for sec in self.secs:
            for i in range(sec.n3d()):
                x = sec.x3d(i)
                y = sec.y3d(i)
                c = h.cos(theta)
                s = h.sin(theta)
                xprime = x * c - y * s
                yprime = x * s + y * c
                sec.pt3dchange(i, xprime, yprime, sec.z3d(i), sec.diam3d(i))

