# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 17:42:54 2014

@author: Dalton
"""
import os
import nipype.interfaces.io as nio
from nipype.algorithms.modelgen import SpecifyModel
from nipype.interfaces import fsl
from nipype.interfaces.fsl.model import Level1Design
from nipype.interfaces.fsl.model import FEATModel


# This dataGrabber can act as an abstraction layer from the filing system
datasource = nio.DataGrabber(infields=['subject_id', 'func_scans'], outfields=['func', 'struct','evs'])
datasource.inputs.base_directory = '/Users/Dalton/Documents/FSL/ValuePilot'
datasource.inputs.subject_id = 710
datasource.inputs.func_scans = [1]
datasource.inputs.template = '*'
datasource.inputs.field_template = dict(func=  'SID%d/Scans/Scan%d*.nii.gz',
                                        struct='SID%d/Scans/co*.nii.gz',
                                        evs=   'SID%d/EVfiles/RUN%d/*.txt')
datasource.inputs.template_args = dict(func=[['subject_id', 'func_scans']],
                                       struct=[['subject_id']],
                                       evs=[['subject_id', 'func_scans']])
datasource.inputs.sort_filelist = False
results = datasource.run()

print results.outputs

cont1 = ['Bundling-Control','T', ['Bundling','Control'],[1,-1]]

s = SpecifyModel()
s.inputs.input_units = 'secs'
s.inputs.functional_runs = results.outputs.func
s.inputs.time_repetition = 2
s.inputs.high_pass_filter_cutoff = 128.
s.inputs.event_files = results.outputs.evs
model = s.run()

level1design = Level1Design()
level1design.inputs.interscan_interval = 2.5
level1design.inputs.bases = {'dgamma':{'derivs': False}}
level1design.inputs.model_serial_correlations = False
level1design.inputs.session_info = model.outputs.session_info
level1design.inputs.contrasts = [cont1]
l1d = level1design.run() 

print l1d.outputs.ev_files
modelgen = FEATModel()
modelgen.inputs.ev_files = l1d.outputs.ev_files
modelgen.inputs.fsf_file = l1d.outputs.fsf_files
model = modelgen.run()

fgls = fsl.FILMGLS()
fgls.inputs.in_file = results.outputs.func
fgls.inputs.design_file = model.outputs.design_file
fgls.inputs.threshold = 10
fgls.inputs.results_dir = 'stats'
res = fgls.run() 
