import time
import numpy as np
from neuron import h
from neuron.units import ms, mV

h.load_file('stdrun.hoc')


class RunSim:
    def __init__(self, init_v, dt=0.025, warmup=0, init_sleep=0, shape_plots=()):
        """
        :param init_v:
            initial value in mV for the neuron function finitialize().
            In many cases it is -70 mV but you need to specify it explicitely
        :param warmup:
            in ms, for warmup with dt=10*ms
        :param init_sleep
            sleep time in seconds. To sleep before first run
        """
        h.finitialize(init_v * mV)
        self.dt = dt
        self.shape_plots = shape_plots

        print("sleep before run for: %s seconds" % init_sleep)
        time.sleep(init_sleep)

        if warmup > 0:
            h.dt = 10
            h.continuerun(warmup * ms)
        h.dt = self.dt

    @property
    def t(self):
        return h.t

    def run(self, runtime, stepsize=None, delay_between_steps=1):
        """
        :param runtime:
            in ms
        :param stepsize:
            in ms. Default None -> stepsize is the size of runtime
        :param delay_between_steps:
            in ms
        """
        if stepsize is None:
            stepsize = runtime

        delay_between_steps = delay_between_steps * 1e-3  # between steps

        # prepare run array
        max_runtime = runtime + self.t

        if runtime == stepsize:
            run_array = [self.t + stepsize]
        else:
            run_array = np.arange(0 + self.t + stepsize, max_runtime, stepsize)
            left_run = max_runtime - max(run_array)
            if left_run > 0:
                run_array = np.concatenate([run_array, [max_runtime]])

        # run main loop
        before = time.time()  # compute time before
        for r in run_array:

            # step till i-th ms
            h.continuerun(r * ms)
            current = time.time()
            computation_time = current - before

            # adjust delay
            delay = delay_between_steps - computation_time
            if delay < 0:
                delay = 0
            time.sleep(delay)
            before = time.time()  # compute time before

            self._plot_shapes()
            print(round(r, 2), "ms", '// comp_time:', round(computation_time * 1000, 2), "ms")

    def _plot_shapes(self):
        # flush shape and console log
        for ps in self.shape_plots:
            ps.fastflush()