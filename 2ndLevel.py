# -*- coding: utf-8 -*-
"""
Created on Mon May 12 17:04:43 2014

@author: Dalton
"""


from nipype.interfaces.fsl import L2Model
model = L2Model(num_copes=3) # 3 sessions
model.run()

from nipype.interfaces import fsl
import os
flameo = fsl.FLAMEO()
                             
flameo.inputs.cope_file='/Users/Dalton/Documents/FSL/ValuePilotTestingL2/FFX/710/copes/_subject_id_710/_conestimate0/cope1.nii.gz'
flameo.inputs.var_cope_file='/Users/Dalton/Documents/FSL/ValuePilotTestingL2/FFX/710/varcopes/_subject_id_710/_conestimate0/varcope1.nii.gz'
#flameo.inputs.cov_split_file='cov_split.mat'
flameo.inputs.design_file='/Users/Dalton/Documents/FSL/ValuePilotTestingL2/designfiles/design.mat'
#flameo.inputs.t_con_file='design.con'
#flameo.inputs.mask_file='mask.nii'
#flameo.inputs.run_mode='fe'

flameo.run()
