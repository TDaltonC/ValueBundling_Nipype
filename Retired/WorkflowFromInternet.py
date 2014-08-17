# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 16:36:07 2014

@author: Dalton
"""

import os                                    # system functions

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model generation
import nipype.algorithms.rapidart as ra      # artifact detection

from nipype.workflows.fmri.fsl import (create_featreg_preproc,
                                  create_modelfit_workflow,
                                  create_fixed_effects_flow)

# The output file format for FSL routines is being set to compressed NIFTI
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

#Name the node for the level1analysis
level1_workflow = pe.Workflow(name='level1flow')

#??????
preproc = create_featreg_preproc(whichvol='first')
#??????
modelfit = create_modelfit_workflow()
#??????
fixed_fx = create_fixed_effects_flow()




