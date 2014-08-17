# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 10:38:27 2014

@author: Dalton
"""

# -*- coding: utf-8 -*-
"""
Created on Fri May  9 10:34:38 2014

@author: Dalton
"""

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

from nipype import config
config.enable_debug_mode()
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

# Templates
mfxTemplateBrain = '/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz'
mniConfig        = '/usr/local/fsl/etc/flirtsch/T1_2_MNI152_2mm.cnf'
mniMask          = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain_mask_dil.nii.gz'


# subject directories
subject_list = ['SID702','SID703','SID705','SID706','SID707','SID708','SID709','SID710'] 

#List of functional scans
func_scan= [1,2,3,4,5]

#ModelSettings
input_units = 'secs'
hpcutoff = 120
TR = 2.

# Contrasts
cont1 = ['Bundling>Control','T', ['Bundling','Control'],[1,-1]]
cont2 = ['Scaling>Task-Even','T', ['Scaling','Control'],[1,-1]]
contrasts = [cont1,cont2]

# Templates
mfxTemplateBrain = '/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz'
mniConfig        = '/usr/local/fsl/etc/flirtsch/T1_2_MNI152_2mm.cnf'

"""
=========
Functions
=========
"""
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



'''
==============
NODES
==============
'''
# MASTER node
masterpipeline = pe.Workflow(name= "MasterWorkfow")
masterpipeline.base_dir = workingdir + 'MFX'
masterpipeline.config = {"execution": {"crashdump_dir":crashRecordsDir}}


# random flow master Node
random_fx = pe.Workflow(name='randomfx')

# 2nd level dataGrabber
contrast_ids = range(0,len(contrasts))
l2source = pe.Node(nio.DataGrabber(infields=['con'],
                                   outfields=['copes', 'varcopes']),
                   name="l2source")

l2source.inputs.base_directory = withinSubjectResults_dir
l2source.inputs.template = '*'
l2source.inputs.field_template= dict(copes=  '*/copes/*/contrast%d/cope1.nii.gz',
                                     varcopes='*/varcopes/*/contrast%d/varcope1.nii.gz')
l2source.inputs.template_args = dict(copes=  [['con']],
                                     varcopes=[['con']])
# iterate over all contrast images

l2source.iterables = [('con',contrast_ids)]
l2source.inputs.sort_filelist = True


#merge the copes and varcopes for each condition
copemerge    = pe.MapNode(interface=fsl.Merge(dimension='t'),
                          iterfield=['in_files'],
                          name="copemerge")
varcopemerge = pe.MapNode(interface=fsl.Merge(dimension='t'),
                       iterfield=['in_files'],
                       name="varcopemerge")

#level 2 model design files (there's one for each contrast)
level2model = pe.Node(interface=fsl.L2Model(),
                      name='l2model')

#estimate a Random FX level model
flameo = pe.MapNode(interface=fsl.FLAMEO(run_mode='fe',
                                         mask_file = mniMask),
                    name="flameo",
                    iterfield=['cope_file','var_cope_file'])

'''
Connections
'''


random_fx.connect([(copemerge,flameo,[('merged_file','cope_file')]),
                  (varcopemerge,flameo,[('merged_file','var_cope_file')]),
                  (level2model,flameo, [('design_mat','design_file'),
                                        ('design_con','t_con_file'),
                                        ('design_grp','cov_split_file')]),
                  ])
                  
masterpipeline.connect([(l2source,random_fx,[('copes','copemerge.in_files'),
                                           ('varcopes','varcopemerge.in_files'),
                                           (('copes', num_copes),'l2model.num_copes'),
                                           ]),

                    ])

                    
if __name__ == '__main__':
    masterpipeline.write_graph(graph2use='hierarchical')    
    masterpipeline.run()