# -*- coding: utf-8 -*-
"""
Created on Tue Apr 22 09:22:20 2014

@author: Dalton
"""
#!/bin/bash
import subprocess

def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash')


bash_command('bet /Users/Dalton/Documents/FSL/Scans/7436BRSID710/DICOM/cos003a1001.nii.gz /Users/Dalton/Documents/FSL/Scans/7436BRSID710/DICOM/cos003a1001_seg_brain')

