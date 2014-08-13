# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 15:54:24 2014

@author: Dalton
"""
from nipype import config #These two lines turn on the debugger
config.enable_debug_mode()

import os                                    # system functions
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine

#Specification of the folder where the dicom-files are located at
experiment_dir = '/Users/Dalton/Documents/FSL/playingWithDICOM'

#Specification of a list containing the identifier of each subject
subjects_list = ['SID710']

#Specification of the name of the dicom and output folder
dicom_dir_name = 'DICOM' #if the path to the dicoms is: '~SOMEPATH/experiment/dicom'
data_dir_name = 'data'   #if the path to the data should be: '~SOMEPATH/experiment/data'

#Node: Infosource - we use IdentityInterface to create our own node, to specify
#                   the list of subjects the pipeline should be executed on
infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                                                      name="infosource")
                                                      
infosource.iterables = ('subject_id', subjects_list)

#Node: DICOMConvert - converts the .dcm files into .nii and moves them into
#                     the folder "data" with a subject specific subfolder
dicom2nifti = pe.Node(interface=fs.DICOMConvert(), name="dicom2nifti")

dicom2nifti.inputs.base_output_dir = experiment_dir + '/' + data_dir_name
#This will store the output to '~SOMEPATH/experiment/data'

dicom2nifti.inputs.file_mapping = [('nifti','*.nii'),('info','dicom.txt'),('dti','*dti.bv*')]
dicom2nifti.inputs.out_type = 'nii'
dicom2nifti.inputs.subject_dir_template = '%s'
dicom2nifti.inputs.ignore_exception = True

#Node ParseDICOMDIR - for creating a nicer nifti overview textfile
dcminfo = pe.Node(interface=fs.ParseDICOMDir(), name="dcminfo")
dcminfo.inputs.sortbyrun = True
dcminfo.inputs.summarize = True
dcminfo.inputs.dicom_info_file = 'nifti_overview.txt'

#Initiation of the preparation pipeline
prepareflow = pe.Workflow(name="prepareflow")

#Define where the workingdir of the all_consuming_workflow should be stored at
prepareflow.base_dir = experiment_dir + '/workingdir_prepareflow'

def pathfinder(subjectname, foldername):
    import os
    experiment_dir = '/Users/Dalton/Documents/FSL/playingWithDICOM'
    return os.path.join(experiment_dir, foldername, subjectname)

#Connect all components
prepareflow.connect([(infosource, dicom2nifti,[('subject_id', 'subject_id')]),
                     (infosource, dicom2nifti,[(('subject_id', pathfinder, dicom_dir_name),
                                                 'dicom_dir')]),
                     (infosource, dcminfo,[(('subject_id', pathfinder, dicom_dir_name),
                                             'dicom_dir')]),
                     ])
                     
prepareflow.write_graph(graph2use='orig')                     
                     
prepareflow.run()