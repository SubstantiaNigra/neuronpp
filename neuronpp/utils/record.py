from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from neuron import h
from neuronpp.core.hocwrappers.seg import Seg


class Record:
    def __init__(self, elements, variables='v'):
        """
        :param elements:
            elements can any object from HocWrappers which implements hoc param
        :param variables:
            str or list_of_str of variable names to track
        """
        if not isinstance(elements, (list, set, tuple)):
            elements = [elements]

        if isinstance(variables, str):
            variables = variables.split(' ')

        if len(elements) == 0:
            raise IndexError("The list of provided elements to record is empty.")

        self.recs = dict([(v, []) for v in variables])
        self.figs = {}
        self.axs = defaultdict(list)

        for elem in elements:
            for var in variables:
                if isinstance(elem, Seg):
                    name = elem.parent.name
                else:
                    name = elem.name
                try:
                    s = getattr(elem.hoc, "_ref_%s" % var)
                except AttributeError:
                    raise AttributeError(
                        "there is no attribute of %s. Maybe you forgot to append loc param for sections?" % var)

                rec = h.Vector().record(s)
                self.recs[var].append((name, rec))

        self.t = h.Vector().record(h._ref_t)

    def plot(self, animate=False, **kwargs):
        """
        :param animate:
            if true, it will redraw the plot on the same figure each time this function is called
        :param steps:
            [used only if animate=True] how many timesteps to see on the graph
        :param y_lim:
            [used only if animate=True] tuple of limits for y axis. Default is (-80, 50)
        :param position:
            position of all subplots ON EACH figure (each figure is created for each variable separately).
            * position=(3,3) -> if you have 9 neurons and want to display 'v' on 3x3 matrix
            * position='merge' -> it will display all figures on the same graph.
            * position=None -> Default, each neuron has separated  axis (row) on the figure.
        :return:
        """
        if animate:
            self._plot_animate(**kwargs)
        else:
            self._plot_static(**kwargs)

    def _plot_static(self, position=None):
        """
        :param position:
            position of all subplots ON EACH figure (each figure is created for each variable separately).
            * position=(3,3) -> if you have 9 neurons and want to display 'v' on 3x3 matrix
            * position='merge' -> it will display all figures on the same graph.
            * position=None -> Default, each neuron has separated  axis (row) on the figure.
        :return:
        """
        for i, (var_name, section_recs) in enumerate(self.recs.items()):
            fig = plt.figure()

            if position is "merge":
                ax = fig.add_subplot(1, 1, 1)

            for i, (name, rec) in enumerate(section_recs):
                rec_np = rec.as_numpy()
                if np.max(np.isnan(rec_np)):
                    raise ValueError(
                        "Vector recorded for variable: '%s' and segment: '%s' contains nan values." % (var_name, name))

                if position is not "merge":
                    ax = self._get_subplot(fig=fig, var_name=var_name, position=position, row_len=len(section_recs),
                                           index=i + 1)
                ax.set_title("Variable: %s" % var_name)
                ax.plot(self.t, rec, label=name)
                ax.set(xlabel='t (ms)', ylabel=var_name)
                ax.legend()

    def _plot_animate(self, steps=10000, y_lim=None, position=None, true_class=None, pred_class=None, stepsize=None,
                      dt=None):
        """
        Call each time you want to redraw plot.

        :param steps:
            how many timesteps to see on the graph
        :param y_lim:
            tuple of limits for y axis. Default is (-80, 50)
        :param position:
            position of all subplots ON EACH figure (each figure is created for each variable separately).
            * position=(3,3) -> if you have 9 neurons and want to display 'v' on 3x3 matrix
            * position='merge' -> it will display all figures on the same graph.
            * position=None -> Default, each neuron has separated  axis (row) on the figure.
        :return:
        """
        create_fig = False
        for var_name, section_recs in self.recs.items():
            if var_name not in self.figs:
                self.figs[var_name] = None

            fig = self.figs[var_name]
            if fig is None:
                create_fig = True
                fig = plt.figure()
                fig.canvas.draw()
                self.figs[var_name] = fig

            for i, (name, rec) in enumerate(section_recs):
                if create_fig:
                    if position == 'merge':
                        ax = fig.add_subplot(1, 1, 1)
                    else:
                        ax = self._get_subplot(fig=fig, var_name=var_name, position=position, row_len=len(section_recs),
                                               index=i + 1)

                    if y_lim:
                        ax.set_ylim(y_lim[0], y_lim[1])
                    line, = ax.plot([], lw=1)
                    # ax.set_title("Variable: %s" % var_name)
                    ax.set_ylabel("{}_{}".format(var_name, i))
                    ax.set_xlabel("t (ms)")
                    ax.legend()

                    self.axs[var_name].append((ax, line))

                ax, line = self.axs[var_name][i]
                t = self.t.as_numpy()[-steps:]
                r = rec.as_numpy()[-steps:]

                ax.set_xlim(t.min(), t.max())
                if y_lim is None:
                    ax.set_ylim(r.min() - (np.abs(r.min() * 0.05)), r.max() + (np.abs(r.max() * 0.05)))

                # update data
                line.set_data(t, r)
                # info draw triangles for true and predicted classes
                true_x, true_y, pred_x, pred_y = self._class_tcks(label=i, true_class=true_class, pred_class=pred_class,
                                                                  t=t, stepsize=stepsize, dt=dt)
                ax.scatter(true_x, true_y, c="orange", marker="^", alpha=0.95)
                ax.scatter(pred_x, pred_y, c="magenta", marker="v", alpha=0.95)

            # info join plots by removing labels and ticks from subplots that are not on the edge
            for key in self.axs:
                for ax in self.axs[key]:
                    ax[0].label_outer()
            fig.subplots_adjust(left=0.09, bottom=0.075, right=0.99, top=0.98, wspace=None, hspace=0.00)
            fig.canvas.draw()
            fig.canvas.flush_events()

        if create_fig:
            plt.show(block=False)

    def _class_tcks(self, label, true_class, pred_class, t, stepsize, dt):
        n = len(true_class)
        x = t[::int(2 * stepsize / dt)][-n:]
        true_x = []
        true_y = []
        pred_x = []
        pred_y = []
        for k in range(n):
            # get the true classes for the current label
            if true_class[k] == label:
                true_x.append(x[k])
                true_y.append(-69)
            if pred_class[k] == label:
                pred_x.append(x[k])
                pred_y.append(30)
        return true_x, true_y, pred_x, pred_y

    def to_csv(self, filename):
        cols = ['time']
        data = [self.t.as_numpy().tolist()]

        for var_name, rec_data in self.recs.items():
            for sec_name, vec in rec_data:
                cols.append(sec_name)
                data.append(vec.as_numpy().tolist())

        df = pd.DataFrame(list(zip(*data)), columns=cols)
        df.to_csv(filename, index=False)

    @staticmethod
    def _get_subplot(fig, var_name, position, row_len=1, index=1):
        if position is None:
            ax = fig.add_subplot(row_len, 1, index)
        elif position == 'grid':
            n = np.sqrt(row_len)
            if n % int(n) != 0:
                n += 1
            ax = fig.add_subplot(n, n, index)
        else:
            size = position[0] * position[1]
            if position[0] * position[1] < row_len:
                raise IndexError("Provided position %s declared %s graphs on the figure, "
                                 "however you have %s records on the variable '%s'." %
                                 (position, size, row_len, var_name))
            ax = fig.add_subplot(position[0], position[1], index)

        return ax
