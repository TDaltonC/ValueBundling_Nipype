# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 09:06:41 2014

@author: Dalton
"""

import os                                    # system functions
import nipype.algorithms.modelgen as model   # model generation
import nipype.algorithms.rapidart as ra      # artifact detection
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.io as nio           # i/o routines
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.base as base        # base routines
import nipype.interfaces.fsl.maths as math   #for dilating of the mask

#To better access the parent folder of the experiment
experiment_dir = '~SOMEPATH/experiment'

#name of the subjects, functional files and output folders
subjects = ['subject1','subject2','subject3']
sessions = ['func1','func2']
nameOfLevel1Out = 'level1_output'

# Tell freesurfer what subjects directory to use
subjects_dir = experiment_dir + '/freesurfer_data'
fs.FSCommand.set_default_subjects_dir(subjects_dir)