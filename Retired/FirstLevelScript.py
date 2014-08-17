# -*- coding: utf-8 -*-
"""
Created on Fri May  9 10:34:38 2014

@author: Dalton
"""


    ##########################
    #####    Imports    ######
    ##########################

from nipype import config #These two lines turn on the debugger
config.enable_debug_mode()

import os
import nipype.interfaces.utility as util #import the utility interface
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe         # the workflow and node wrappers
from nipype.algorithms.modelgen import SpecifyModel
from nipype.interfaces import fsl
from nipype.interfaces.fsl.model import Level1Design
from nipype.interfaces.fsl.model import FEATModel


    #####################################
    #####  Config & Model Settings  #####
    #####################################

##
#Model Settings
TR = 2.
high_pass = 128.
modelSerialCorrelations = True
subjects = ['710','709']

    #Contrasts
cont1 = ('Bundling-Control','T', ['Bundling','Control'],[1,-1])
cont2 = ('Control-Bundling','T', ['Bundling','Control'],[-1,1])
conts = [cont1,cont2]


##
# Config
experiment_dir = '/Users/Dalton/Documents/FSL/ValuePilot'
firstLevelResults_dir ='/Users/Dalton/Documents/FSL/ValuePilot/FFX'

    ##########################
    #####    NODES!!!   ######
    ##########################

# NODE infosource --- This is used to iterate over all of the subjects
infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")
    #define the list of subjects your pipeline should be executed on
infosource.iterables = ('subject_id', subjects)

# NODE dataGrabber --- act as an abstraction layer from the filing system
datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'func_scans'],
                                               outfields=['func', 'struct','evs']),
                     name="datasource")
datasource.inputs.base_directory = experiment_dir
datasource.inputs.func_scans = [1,2,3,4,5]
datasource.inputs.template = '*'
datasource.inputs.field_template = dict(func=  'RawData/SID%s/niis/Scan%d*.nii',
                                        struct='RawData/SID%s/niis/co*.nii',
                                        evs=   'RawData/SID%s/EVfiles/RUN%d/*.txt')
datasource.inputs.template_args = dict(func=[['subject_id', 'func_scans']],
                                       struct=[['subject_id']],
                                       evs=[['subject_id', 'func_scans']])
datasource.inputs.sort_filelist = False

# NODE DataSink --- stores important outputs
datasink = pe.Node(interface=nio.DataSink(), name="datasink")
datasink.inputs.base_directory = firstLevelResults_dir
#datasink.inputs.parameterization = False # This line keeps the DataSink from adding an aditional level to the directory, I have no Idea why this works.  

#NODE SpecifyModel --- generate design information.
modelspec = pe.Node(interface=SpecifyModel(),  name="modelspec")
modelspec.inputs.input_units = 'secs'
modelspec.inputs.time_repetition = TR
modelspec.inputs.high_pass_filter_cutoff = high_pass

# NODE Level1Design --- generate a run specific fsf file for analysis
level1design = pe.Node(interface=fsl.Level1Design(interscan_interval = TR,
                                                  model_serial_correlations = modelSerialCorrelations,
                                                  bases = {'dgamma':{'derivs': False}},
                                                  contrasts = conts),
                       name="level1design",
                      )

#NODE FEATModel --- generate a run specific mat file for use by FILMGLS
modelgen = pe.MapNode(interface=fsl.FEATModel(),
                      name='modelgen',
                      iterfield = ['fsf_file', 'ev_files'],
                      )

#NODE FILMGLS --- estimate the model specified by a mat file and a functional run
modelestimate = pe.MapNode(interface=fsl.FILMGLS(smooth_autocorr=True,
                                                 mask_size=5,
                                                 threshold=1000),
                           name='modelestimate',
                           iterfield = ['design_file', 'in_file']
                           )
                           
# NODE ContrastMgr --- generate contrast estimates
conestimate = pe.MapNode(interface=fsl.ContrastMgr(), name='conestimate',
                         iterfield = ['tcon_file','param_estimates',
                                      'sigmasquareds', 'corrections',
                                      'dof_file'])


    ##########################
    #####   Workflows   ######
    ##########################


modelfit = pe.Workflow(name='modelfit')


    ############################
    #####   Connections   ######
    ############################


modelfit.connect([
    (infosource, datasource,[('subject_id','subject_id')]),
    (datasource,modelspec,[('func','functional_runs'),
                           ('evs','event_files')]), 
   (modelspec,level1design,[('session_info','session_info')]),
   (level1design,modelgen,[('fsf_files', 'fsf_file'),
                           ('ev_files', 'ev_files')]),
   (modelgen,modelestimate,[('design_file','design_file')]),
   (datasource,modelestimate,[('func','in_file')]),
   (modelgen,conestimate,[('con_file','tcon_file')]),
   (modelestimate,conestimate,[('param_estimates','param_estimates'),
                               ('sigmasquareds', 'sigmasquareds'),
                               ('corrections','corrections'),
                               ('dof_file','dof_file')]),
    #DataSink COnnections 
   (infosource, datasink, [('subject_id', 'container')]),
   (modelestimate,datasink,[('corrections','corrections')]),
   (level1design,datasink,[('fsf_files', 'fsf_file')]),
   (conestimate,datasink,[('tstats','tstats'),
                          ('copes','copes'),
                          ('varcopes','varcopes')])
   ])

    ############################
    #####       RUN       ######
    ############################

modelfit.write_graph(graph2use='orig')

modelfit.run(plugin='MultiProc')