from os import path
from neuron import h

from neuronpp.core.cells.core_cell import CoreCell
from neuronpp.core.hocwrappers.sec import Sec

h.load_file('stdlib.hoc')
h.load_file('import3d.hoc')


class SectionCell(CoreCell):
    def __init__(self, name=None, compile_paths=None):
        """
        :param name:
            Name of the cell
        """
        CoreCell.__init__(self, name, compile_paths=compile_paths)
        # if Cell (named core_cell) have been built before on the stack of super() objects
        if not hasattr(self, '_core_cell_builded'):
            self.secs = []
            self._core_cell_builded = True

    def filter_secs(self, name=None, **kwargs):
        """
        :param name:
            start with 'regex:any pattern' to use regular expression. If without 'regex:' - will look which Hoc objects contain the str
        :return:
        """
        return self.filter(searchable=self.secs, name=name, **kwargs)

    def insert(self, mechanism_name: str, sec=None):
        if isinstance(sec, Sec):
            sec = [sec]
        elif sec is None or isinstance(sec, str):
            sec = self.filter_secs(name=sec)

        for se in sec:
            se.hoc.insert(mechanism_name)
        return self

    def add_sec(self, name: str, diam=None, l=None, nseg=1):
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

        if len(self.filter_secs(name)) > 0:
            raise LookupError("The name '%s' is already taken by another section of the cell: '%s' of type: '%s'."
                              % (name, self.name, self.__class__.__name__))
        sec = Sec(hoc_sec, parent=self, name=name)
        self.secs.append(sec)
        return sec

    def connect_secs(self, source, target, source_loc=1.0, target_loc=0.0):
        """
        default: source(0.0) -> target(1.0)

        If you specify 1.0 for source_loc or target_loc it will assume 0.999 loc instead. This is because NEURON do not
        insert any mechanisms to the 1.0 end (it is dimension-less). NEURON allows to connect section to the 1.0,
        however this raise problems while copying parameters between sections. So any 1.0 loc will be changed to 0.999
        instead.
        :param source:
        :param target:
        :param source_loc:
        :param target_loc:
        :return:
        """
        if source_loc > 1.0 or source_loc < 0.0:
            raise ValueError("source_loc param must be in range [0,1]")
        if target_loc > 1.0 or target_loc < 0.0:
            raise ValueError("target_loc param must be in range [0,1]")

        if source is None or target is None:
            raise LookupError("source and target must be specified. Can't be None.")

        if isinstance(source, str):
            source = self.filter_secs(name=source)
            if isinstance(source, list):
                raise LookupError("To connect sections source name must return exactly 1 Section, "
                                  "but returned %s elements for name=%s" % (len(source), source))

        if isinstance(target, str) or target is None:
            target = self.filter_secs(name=target)
            if isinstance(target, list):
                raise LookupError("To connect sections target name must return exactly 1 Section, "
                                  "but returned %s elements for name=%s" % (len(source), source))

        target_loc = float(target_loc)
        source_loc = float(source_loc)

        source.hoc.connect(target.hoc(source_loc), target_loc)

    def load_morpho(self, filepath):
        """
        :param filepath:
            swc file path
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
        i3d = h.Import3d_GUI(morpho, 0)
        i3d.instantiate(self)

        for hoc_sec in self.all:
            name = hoc_sec.name().split('.')[-1]  # eg. name="dend[19]"
            if len(self.filter_secs(name)) > 0:
                raise LookupError("The name '%s' is already taken by another section of the cell: '%s' of type: '%s'."
                                  % (name, self.name, self.__class__.__name__))
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

    def copy_mechanisms(self, secs_to, sec_from='parent'):
        """
        Copy mechanisms from the sec_from to all sections specified in the secs_to param.
        If sec_from is 'parent' it will copy mechanisms from the parent of each sections in the secs_to param.
        """
        for sec in secs_to:

            if sec_from == 'parent':
                segment_from = sec.hoc.psection()['morphology']['parent']
                current_sec_from = segment_from.sec
            elif isinstance(sec_from, Sec):
                current_sec_from = sec_from.hoc
                segment_from = self._get_first_segment(current_sec_from)
            else:
                raise TypeError("The param sec_from can be only type of Sec or string 'parent', "
                                "but provided %s" % sec_from)

            all_mechs = current_sec_from.psection()['density_mechs']

            if segment_from.x == 1.0:
                segment_from = current_sec_from(0.999)
            if segment_from.x == 0:
                segment_from = current_sec_from(0.001)

            for mech_name, params in all_mechs.items():
                self.insert(mech_name, sec)
                from_mech = getattr(segment_from, mech_name)

                for param_name in params.keys():
                    value = getattr(from_mech, param_name)

                    for to_segment in sec.hoc:
                        to_mech = getattr(to_segment, mech_name)

                        try:
                            setattr(to_mech, param_name, value)
                        except ValueError:
                            continue

    @staticmethod
    def _hasmech(sec: Sec, mech_name: str):
        for s in sec.hoc:
            return hasattr(s, mech_name)

    @staticmethod
    def _get_first_segment(sec: Sec):
        for s in sec.hoc:
            return s

