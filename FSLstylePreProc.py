# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 12:42:49 2014

@author: Dalton
"""
#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
=========
Imports
=========
"""
import os                                    # system functions

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model generation
import nipype.algorithms.rapidart as ra      # artifact detection


"""
==============
Configurations
==============
"""
#set output file format to compressed NIFTI.
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

# Wthere the input data comes from
data_dir =                os.path.abspath('../RawData')
# Where the outputs goes
withinSubjectResults_dir =os.path.abspath('../FFX')
# Working Directory
workingdir =              os.path.abspath('../fslWorkingDir/workingdir')
# Crash Records
crashRecordsDir =         os.path.abspath('../fslWorkingDir/crashdumps')

# subject directories
subject_list = ['SID702','SID703','SID705','SID706','SID707','SID708','SID709','SID710'] 

#List of functional scans
func_scan= [1,2,3,4,5]

#ModelSettings
input_units = 'secs'
hpcutoff = 120
TR = 2.

#Contrasts
cont1 = ['Bundling>Control','T', ['Bundling','Control'],[1,-1]]
cont2 = ['Scaling>Task-Even','T', ['Scaling','Control'],[1,-1]]
contrasts = [cont1,cont2]

"""
=========
Functions
=========
"""
#function to pick the first file from a list of files
def pickfirst(files):
    if isinstance(files, list):
        return files[0]
    else:
        return files
        
#function to return the 1 based index of the middle volume
def getmiddlevolume(func):
    from nibabel import load
    funcfile = func
    if isinstance(func, list):
        funcfile = func[0]
    _,_,_,timepoints = load(funcfile).get_shape()
    return (timepoints/2)-1

#function to get the scaling factor for intensity normalization
def getinormscale(medianvals):
    return ['-mul %.10f'%(10000./val) for val in medianvals]

#function to get 10% of the intensity
def getthreshop(thresh):
    return '-thr %.10f -Tmin -bin'%(0.1*thresh[0][1])

#functions to get the brightness threshold for SUSAN
def getbtthresh(medianvals):
    return [0.75*val for val in medianvals]
    
def getusans(x):
    return [[tuple([val[0],0.75*val[1]])] for val in x]

#Function to Sort Copes
def sort_copes(files):
    numelements = len(files[0])
    outfiles = []
    for i in range(numelements):
        outfiles.insert(i,[])
        for j, elements in enumerate(files):
            outfiles[i].append(elements[i])
    return outfiles
    
def num_copes(files):
    return len(files)


"""
=======================
preprocessing workflow
=======================

NODES
"""
#Master node
preproc = pe.Workflow(name='preproc')

#inout utility node
inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                             'struct',]),
                    name='inputspec')

#Convert functional images to floats.
#use a MapNode to paralelize
img2float = pe.MapNode(interface=fsl.ImageMaths(out_data_type='float',
                                             op_string = '',
                                             suffix='_dtype'),
                       iterfield=['in_file'],
                       name='img2float')

#Extract the middle volume of the first run as the reference
extract_ref = pe.Node(interface=fsl.ExtractROI(t_size=1),
                      name = 'extractref')

#Realign the functional runs to the middle volume of the first run
motion_correct = pe.MapNode(interface=fsl.MCFLIRT(save_mats = True,
                                                  save_plots = True),
                            name='realign',
                            iterfield = ['in_file'])
                            
#Plot the estimated motion parameters
plot_motion = pe.MapNode(interface=fsl.PlotMotionParams(in_source='fsl'),
                        name='plot_motion',
                        iterfield=['in_file'])
plot_motion.iterables = ('plot_type', ['rotations', 'translations'])

#Extract the mean volume of the first functional run
meanfunc = pe.Node(interface=fsl.ImageMaths(op_string = '-Tmean',
                                            suffix='_mean'),
                   name='meanfunc')

#Strip the skull from the mean functional
meanfuncmask = pe.Node(interface=fsl.BET(mask = True,
                                         no_output=True,
                                         frac = 0.3,
                                         robust = True),
                       name = 'meanfuncmask')

#Mask the functional runs with the extracted mask
maskfunc = pe.MapNode(interface=fsl.ImageMaths(suffix='_bet',
                                               op_string='-mas'),
                      iterfield=['in_file'],
                      name = 'maskfunc')

#Determine the 2nd and 98th percentile intensities of each functional run
getthresh = pe.MapNode(interface=fsl.ImageStats(op_string='-p 2 -p 98'),
                       iterfield = ['in_file'],
                       name='getthreshold')
                       
#Threshold the first run of the functional data at 10% of the 98th percentile
threshold = pe.Node(interface=fsl.ImageMaths(out_data_type='char',
                                             suffix='_thresh'),
                    name='threshold')

#Determine the median value of the functional runs using the mask
medianval = pe.MapNode(interface=fsl.ImageStats(op_string='-k %s -p 50'),
                       iterfield = ['in_file'],
                       name='medianval')

#Dilate the mask
dilatemask = pe.Node(interface=fsl.ImageMaths(suffix='_dil',
                                              op_string='-dilF'),
                     name='dilatemask')

#Mask the motion corrected functional runs with the dilated mask
maskfunc2 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                op_string='-mas'),
                       iterfield=['in_file'],
                       name='maskfunc2')
                       
#Determine the mean image from each functional run
meanfunc2 = pe.MapNode(interface=fsl.ImageMaths(op_string='-Tmean',
                                                suffix='_mean'),
                       iterfield=['in_file'],
                       name='meanfunc2')

#Merge the median values with the mean functional images into a coupled list
mergenode = pe.Node(interface=util.Merge(2, axis='hstack'),
                    name='merge')

#Smooth each run using SUSAN 
#brightness threshold set to xx% of the median value for each run by function 'getbtthresh'
#and a mask constituting the mean functional
smooth = pe.MapNode(interface=fsl.SUSAN(fwhm = 5.),
                    iterfield=['in_file', 'brightness_threshold','usans'],
                    name='smooth'
                    )

#Mask the smoothed data with the dilated mask
maskfunc3 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                op_string='-mas'),
                       iterfield=['in_file'],
                       name='maskfunc3')

#Scale each volume of the run so that the median value of the run is set to 10000
intnorm = pe.MapNode(interface=fsl.ImageMaths(suffix='_intnorm'),
                     iterfield=['in_file','op_string'],
                     name='intnorm')

#Perform temporal highpass filtering on the data
highpass = pe.MapNode(interface=fsl.ImageMaths(suffix='_hpf',
                                               op_string = '-bptf %d -1'%(hpcutoff/TR)),
                      iterfield=['in_file'],
                      name='highpass')

#Generate a mean functional image from the first run
meanfunc3 = pe.MapNode(interface=fsl.ImageMaths(op_string='-Tmean',
                                                suffix='_mean'),
                       iterfield=['in_file'],
                       name='meanfunc3')

#Skull Strip the structural image
nosestrip = pe.Node(interface=fsl.BET(frac=0.3),
                    name = 'nosestrip')
skullstrip = pe.Node(interface=fsl.BET(mask = True, robust = True),
                     name = 'stripstruct')

#register the mean functional image to the structural image
coregister = pe.Node(interface=fsl.FLIRT(dof=6),
                     name = 'coregister')

#Find outliers based on deviations in intensity and/or movement.
art = pe.MapNode(interface=ra.ArtifactDetect(use_differences = [True, False],
                                             use_norm = True,
                                             norm_threshold = 1,
                                             zintensity_threshold = 3,
                                             parameter_source = 'FSL',
                                             mask_type = 'file'),
                 iterfield=['realigned_files', 'realignment_parameters'],
                 name="art")
"""
Connections
"""
preproc.connect(inputnode, 'func', img2float, 'in_file')
preproc.connect(img2float, ('out_file', pickfirst), extract_ref, 'in_file')
preproc.connect(inputnode, ('func', getmiddlevolume), extract_ref, 't_min')
preproc.connect(img2float, 'out_file', motion_correct, 'in_file')
preproc.connect(extract_ref, 'roi_file', motion_correct, 'ref_file')
preproc.connect(motion_correct, 'par_file', plot_motion, 'in_file')
preproc.connect(motion_correct, ('out_file', pickfirst), meanfunc, 'in_file')
preproc.connect(meanfunc, 'out_file', meanfuncmask, 'in_file')
preproc.connect(motion_correct, 'out_file', maskfunc, 'in_file')
preproc.connect(meanfuncmask, 'mask_file', maskfunc, 'in_file2')
preproc.connect(maskfunc, 'out_file', getthresh, 'in_file')
preproc.connect(maskfunc, ('out_file', pickfirst), threshold, 'in_file')
preproc.connect(getthresh, ('out_stat', getthreshop), threshold, 'op_string')
preproc.connect(motion_correct, 'out_file', medianval, 'in_file')
preproc.connect(threshold, 'out_file', medianval, 'mask_file')
preproc.connect(threshold, 'out_file', dilatemask, 'in_file')
preproc.connect(motion_correct, 'out_file', maskfunc2, 'in_file')
preproc.connect(dilatemask, 'out_file', maskfunc2, 'in_file2')
preproc.connect(maskfunc2, 'out_file', meanfunc2, 'in_file')
preproc.connect(medianval, ('out_stat', getinormscale), intnorm, 'op_string')
preproc.connect(meanfunc2,'out_file', mergenode, 'in1')
preproc.connect(medianval,'out_stat', mergenode, 'in2')
preproc.connect(maskfunc2, 'out_file', smooth, 'in_file')
preproc.connect(medianval, ('out_stat', getbtthresh), smooth, 'brightness_threshold')
preproc.connect(mergenode, ('out', getusans), smooth, 'usans')
preproc.connect(smooth, 'smoothed_file', maskfunc3, 'in_file')
preproc.connect(dilatemask, 'out_file', maskfunc3, 'in_file2')
preproc.connect(maskfunc3, 'out_file', intnorm, 'in_file')
preproc.connect(intnorm, 'out_file', highpass, 'in_file')
preproc.connect(highpass, ('out_file', pickfirst), meanfunc3, 'in_file')
preproc.connect([(inputnode, nosestrip,[('struct','in_file')]),
                 (nosestrip, skullstrip, [('out_file','in_file')]),
                 (skullstrip, coregister,[('out_file','in_file')]),
                 (meanfunc2, coregister,[(('out_file',pickfirst),'reference')]),
                 (motion_correct, art, [('par_file','realignment_parameters')]),
                 (maskfunc2, art, [('out_file','realigned_files')]),
                 (dilatemask, art, [('out_file', 'mask_file')]),
                 ])

"""
======================
model fitting workflow
======================

NODES
"""
#Master Node
modelfit = pe.Workflow(name='modelfit')

#generate design information
modelspec = pe.Node(interface=model.SpecifyModel(input_units = input_units,
                                                 time_repetition = TR,
                                                 high_pass_filter_cutoff = hpcutoff),
                    name="modelspec")

#generate a run specific fsf file for analysis
level1design = pe.Node(interface=fsl.Level1Design(interscan_interval = TR,
                                                  bases = {'dgamma':{'derivs': False}},
                                                  contrasts = contrasts,
                                                  model_serial_correlations = True),
                       name="level1design")

#generate a run specific mat file for use by FILMGLS
modelgen = pe.MapNode(interface=fsl.FEATModel(), name='modelgen',
                      iterfield = ['fsf_file', 'ev_files'])

#estomate Model
modelestimate = pe.MapNode(interface=fsl.FILMGLS(smooth_autocorr=True,
                                                 mask_size=5,
                                                 threshold=1000),
                                                 name='modelestimate',
                                                 iterfield = ['design_file',
                                                              'in_file'])

#estimate contrasts
conestimate = pe.MapNode(interface=fsl.ContrastMgr(), name='conestimate',
                         iterfield = ['tcon_file','param_estimates',
                                      'sigmasquareds', 'corrections',
                                      'dof_file'])

'''
CONNECTIONS
'''
modelfit.connect([
   (modelspec,level1design,[('session_info','session_info')]),
   (level1design,modelgen,[('fsf_files', 'fsf_file'),
                           ('ev_files', 'ev_files')]),
   (modelgen,modelestimate,[('design_file','design_file')]),
   (modelgen,conestimate,[('con_file','tcon_file')]),
   (modelestimate,conestimate,[('param_estimates','param_estimates'),
                               ('sigmasquareds', 'sigmasquareds'),
                               ('corrections','corrections'),
                               ('dof_file','dof_file')]),
   ])

"""
======================
fixed-effects workflow
======================

NODES
"""
# Master Node
fixed_fx = pe.Workflow(name='fixedfx')

#merge the copes and varcopes for each condition
copemerge    = pe.MapNode(interface=fsl.Merge(dimension='t'),
                          iterfield=['in_files'],
                          name="copemerge")
varcopemerge = pe.MapNode(interface=fsl.Merge(dimension='t'),
                       iterfield=['in_files'],
                       name="varcopemerge")

#level 2 model design files (there's one for each condition of each subject)
level2model = pe.Node(interface=fsl.L2Model(),
                      name='l2model')

#estimate a second level model
flameo = pe.MapNode(interface=fsl.FLAMEO(run_mode='fe'), name="flameo",
                    iterfield=['cope_file','var_cope_file'])

'''
Connections
'''
fixed_fx.connect([(copemerge,flameo,[('merged_file','cope_file')]),
                  (varcopemerge,flameo,[('merged_file','var_cope_file')]),
                  (level2model,flameo, [('design_mat','design_file'),
                                        ('design_con','t_con_file'),
                                        ('design_grp','cov_split_file')]),
                  ])


"""
=======================
Within-Subject workflow
=======================

NODES
"""
#Master NODE
withinSubject = pe.Workflow(name='withinSubject')

"""
CONNECTIONS
"""
withinSubject.connect([(preproc, modelfit,[('highpass.out_file', 'modelspec.functional_runs'),
                                           ('art.outlier_files', 'modelspec.outlier_files'),
                                           ('highpass.out_file','modelestimate.in_file')]),
                      (preproc, fixed_fx, [('coregister.out_file', 'flameo.mask_file')]),
                      (modelfit, fixed_fx,[(('conestimate.copes', sort_copes),'copemerge.in_files'),
                                           (('conestimate.varcopes', sort_copes),'varcopemerge.in_files'),
                                           (('conestimate.copes', num_copes),'l2model.num_copes'),
                                           ]),

                    ])
                    
                    
                    
"""
=============
META workflow
=============

NODES
"""
# Master NODE
l1pipeline = pe.Workflow(name= "level1")
l1pipeline.base_dir = workingdir
l1pipeline.config = {"execution": {"crashdump_dir":crashRecordsDir}}

# Set up inforsource to iterate over 'subject_id's
infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")
infosource.iterables = ('subject_id', subject_list)

# The datagrabber finds all of the files that need to be run and makes sure that
# they get to the right nodes at the benining of the protocol.
datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['func', 'struct','evs']),
                     name = 'datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = '*'
datasource.inputs.field_template= dict(func=  '%s/niis/Scan%d*.nii',
                                       struct='%s/niis/co%s*.nii',
                                       evs=   '%s/EVfiles/RUN%d/*.txt')
datasource.inputs.template_args = dict(func=  [['subject_id', func_scan]],
                                       struct=[['subject_id','t1mprage']],
                                       evs =  [['subject_id', func_scan]])
datasource.inputs.sort_filelist = True



#DataSink  --- stores important outputs
datasink = pe.Node(interface=nio.DataSink(base_directory= withinSubjectResults_dir,
                                          parameterization = True # This line keeps the DataSink from adding an aditional level to the directory, I have no Idea why this works.
                                          
                                          ),
                   name="datasink")
datasink.inputs.substitutions = [('_subject_id_', ''),
                                 ('_flameo', 'contrast')]


"""
CONNECTIONS
"""

l1pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                    (datasource, withinSubject, [('evs', 'modelfit.modelspec.event_files')]),
                    (datasource, withinSubject, [('struct','preproc.inputspec.struct'),
                                              ('func', 'preproc.inputspec.func'),
                                              ]),
                    (infosource, datasink, [('subject_id', 'container')])
                    ])
                    
#DataSink Connections -- These are put with the meta flow becuase the dataSink 
                       # reaches in to a lot of deep places, but it is not of 
                       # those places; hence META.
withinSubject.connect([(modelfit,datasink,[('modelestimate.param_estimates','regressorEstimates')]),
                      (modelfit,datasink,[('level1design.fsf_files', 'fsf_file')]),
                      (fixed_fx,datasink,[('flameo.tstats','tstats'),
                                          ('flameo.copes','copes'),
                                          ('flameo.var_copes','varcopes')])
                       ])


"""
====================
Execute the pipeline
====================
"""

if __name__ == '__main__':
    # Plot a network visualization of the pipline
    l1pipeline.write_graph(graph2use='hierarchical')
#    # Run the paipline using 1 CPUs
#    outgraph = l1pipeline.run()    
    # Run the paipline using 8 CPUs
    outgraph = l1pipeline.run(plugin='MultiProc', plugin_args={'n_procs':8})
    l2pipeline.run('MultiProc')
