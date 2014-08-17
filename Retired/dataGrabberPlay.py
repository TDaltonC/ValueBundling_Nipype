# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 09:39:17 2014

@author: Dalton
"""

import os
import nipype.interfaces.io as nio

datasource = nio.DataGrabber(infields=['subject_id', 'func_scans'], outfields=['func', 'struct','evs'])
datasource.inputs.base_directory = '/Users/Dalton/Documents/FSL/ValuePilot'
datasource.inputs.subject_id = 710
datasource.inputs.func_scans = [1,2,3,4,5]
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