# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 17:39:28 2020

@author: Wladek
"""
from neuronpp.core.hocwrappers.seg import Seg
import numpy as np
import matplotlib.pyplot as py
from neuronpp.core.hocwrappers.point_process import PointProcess

class PlotNetworkStatus:
    def __init__(self, cells, weight_name='w'):
        self.cells = cells
        self.edges =[]
        self.colors = []
        self.texts = []
        self.lines = []
        self.x_list = []
        self.y_list = []
        self.correct_position = (0.1, 0.1)
        self._pops_iterate(weight_name)
    
    def _pops_iterate(self, weight_name):
        for c in self.cells:
            if 'mot' in c.name: continue
            soma = c.filter_secs('soma')
            c.make_spike_detector(soma(0.5))
            split_name = c.name.split('[')
            x_pos = int(split_name[0][-1])
            y_pos = int(split_name[-1][:-1])
            
            if 'inh' in c.name: 
                self.colors.append('red')
                y_pos -= 5
            elif 'hid' in c.name: self.colors.append('blue')
            else: self.colors.append('green') 
            self.x_list.append(x_pos)
            self.y_list.append(y_pos)
            self.edges.append(self._find_target(c, x_pos, y_pos, weight_name))
        self.plot_graph() 
        
    def _find_target(self, c, x_pos, y_pos, weight_name):
        targets = []
        for nc in c.ncs:
            if "SpikeDetector" in nc.name:
                continue
            elif isinstance(nc.source, Seg) and isinstance(nc.target, PointProcess) and hasattr(nc.target.hoc, weight_name):
                split_target = nc.source.parent.parent.name.split('[')
                x_trg = int(split_target[0][-1])
                y_trg = int(split_target[-1][:-1])
                weight = getattr(nc.target.hoc, weight_name)
                targets.append([[x_pos,x_trg], [y_pos, y_trg], weight])
        return targets
    
    def _find_weights(self, c, weight_name):
        targets = []
        for nc in c.ncs:
            if "SpikeDetector" in nc.name:
                continue
            elif isinstance(nc.source, Seg) and isinstance(nc.target, PointProcess) and hasattr(nc.target.hoc, weight_name):
                weight = getattr(nc.target.hoc, weight_name)
                targets.append(weight)
        return targets
                
    def plot_graph(self):
        py.figure()
        ax2 = py.subplot(111)
        self.dots=[]
        for cell_num,edge in enumerate(self.edges): 
            self.dots.append(ax2.scatter(self.x_list[cell_num],
                                         self.y_list[cell_num], s=300, 
                                         color=self.colors[cell_num], alpha=0.5))
            for target in edge:
                line, = ax2.plot(target[0], target[1], lw = target[2], color='grey')
                self.lines.append(line)
        n=0
        for c in self.cells: 
            if 'mot' in c.name: continue
            self.texts.append(ax2.text(self.x_list[n]-self.correct_position[0], 
                                       self.y_list[n]-self.correct_position[1], '')) 
            n+=1
        ax2.spines['right'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        py.xticks([0,1,2,3], ['Input', 'Hidden', 'Inhibitory', 'Output'])
    
    def update_weights(self, weight_name):
        n=0
        for c in self.cells: 
            for target in self._find_weights(c, weight_name):
                self.lines[n].set_linewidth(target)
                n+=1
                py.draw()
                
    def update_spikes(self, sim_time):
        n=0
        for c in self.cells:
            if 'mot' in c.name: 
                continue
            spikes = np.asarray(c.get_spikes())
            self.texts[n].set_text(str(spikes.shape[0]))
            alpha = spikes>(sim_time-50)
            if 'inp' in c.name: 
                print(alpha)
                print(spikes)
            self.dots[n].set_alpha(np.sum(alpha)/10)
            n+=1
            py.draw()