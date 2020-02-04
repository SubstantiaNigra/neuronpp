from collections import defaultdict

from neuronpp.core.cells.netstim_cell import NetStimCell

from neuronpp.core.cells.netconn_cell import NetConnCell
from neuronpp.core.hocwrappers.composed.synapse import Synapse


class SynapticCell(NetConnCell):
    def __init__(self, name=None, compile_paths=None):
        NetConnCell.__init__(self, name, compile_paths=compile_paths)
        self.syns = []
        self._syn_num = defaultdict(int)

    def filter_synapses(self, mod_name: str = None, name=None, source=None, point_process=None, parent=None, tag=None, **kwargs):
        """
        :param mod_name:
            single string defining name of point process type name, eg. concere synaptic mechanisms like Syn4PAChDa
        :param name:
            start with 'regex:any pattern' to use regular expression. If without 'regex:' - will look which Hoc objects contain the str
        :param source:
            string of source compound name (if source is provided)
        :param point_process:
            string of point process compound name
        :return:
        """
        return self.filter(self.syns, mod_name=mod_name, name=name, source=source, point_process=point_process, parent=parent,
                           tag=tag, **kwargs)

    def make_sypanses(self, source, mod_name: str, weight=1, rand_weight=False, tag: str = None, target_sec=None, source_loc=None, target_loc=0.0,
                      delay=0, threshold=10, **synaptic_params):
        """

        :param source:
            Can be only: hocwrappers.NetStim, hocwrappers.VecStim, hocwrappers.Sec or None. If it is Sec also loc param need to be defined.
            If None it will create NetConn with no source, which can be use as external event source
        :param weight:
        :param rand_weight:
            if True, will find rand weight [0,1) and multiply this by weight.
        :param tag:
        :param mod_name:
        :param target_sec:
        :param source_loc:
        :param target_loc:
        :param delay:
        :param threshold:
        :param synaptic_params:
        :return:
        """

        pps = self.make_point_processes(tag=tag, mod_name=mod_name, sec=target_sec, loc=target_loc, **synaptic_params)
        nns = self.make_netcons(source=source, source_loc=source_loc, weight=weight, mod_name=mod_name, point_process=pps,
                                rand_weight=rand_weight, delay=delay, threshold=threshold)

        result = []
        for p, n in zip(pps, nns):
            i = self._syn_num[p.mod_name]
            self._syn_num[p.mod_name] += 1

            syn = Synapse(source, point_process=p, netconn=n, parent_sec=p.parent, name=str(i), tag=tag)
            self.syns.append(syn)
            result.append(syn)

        return result
