# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 16:57:37 2014

@author: Dalton
"""
import nipype
from nipype.interfaces import fsl
import nipype.pipeline.engine as pe
from nipype.algorithms.modelgen import SpecifyModel

Struc_scan = '/Users/Dalton/Documents/FSL/ValuePilot/7436BRSID710/Scans/20140312_134726t2w4radiologys002a1001.nii.gz'
func_scans = '/Users/Dalton/Documents/FSL/ValuePilot/7436BRSID710/Scans/20140312_134726Scan1s004a001.nii.gz'


skullstrip = pe.Node(fsl.BET(in_file=Struc_scan, robust = True), name="skullstrip")


