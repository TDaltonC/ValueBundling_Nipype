# -*- coding: utf-8 -*-
"""
Created on Fri May  2 13:21:15 2014

@author: Dalton
"""

from nipype.interfaces.freesurfer import ParseDICOMDir
from nipype.interfaces.freesurfer import DICOMConvert

dcminfo = ParseDICOMDir()
dcminfo.inputs.dicom_dir = '/Users/Dalton/Documents/FSL/playingWithDICOM/DICOM/SID710/DICOM/14031214/50480000'
dcminfo.inputs.sortbyrun = True
dcminfo.inputs.summarize = True
dcminfo.run()



cvt = DICOMConvert()
cvt.inputs.dicom_dir = '/Users/Dalton/Documents/FSL/playingWithDICOM/DICOM/SID710/DICOM/14031214/50480000'
cvt.inputs.base_output_dir = '/Users/Dalton/Documents/FSL/playingWithDICOM/data/SID710'

cvt.run()