# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 10:38:27 2014

@author: Dalton
"""

# 2nd level dataGrabber
contrast_ids = range(1,len(contrasts)+1)
l2source = pe.Node(nio.DataGrabber(infields=['con']), name="l2source")
l2source.inputs.template=os.path.abspath('spm_tutorial/l1output/*/con*/*/_fwhm_%d/con_%04d.img')
# iterate over all contrast images
l2source.iterables = [('con',contrast_ids)]
l2source.inputs.sort_filelist = True

# 1-sample t-test
onesamplettestdes = pe.Node(interface=spm.OneSampleTTestDesign(), name="onesampttestdes")
l2estimate = pe.Node(interface=spm.EstimateModel(), name="level2estimate")
l2estimate.inputs.estimation_method = {'Classical' : 1}
l2conestimate = pe.Node(interface = spm.EstimateContrast(), name="level2conestimate")
cont1 = ('Group','T', ['mean'],[1])
l2conestimate.inputs.contrasts = [cont1]
l2conestimate.inputs.group_contrast = True

# Connections

l2pipeline = pe.Workflow(name="level2")
l2pipeline.base_dir = os.path.abspath('spm_tutorial/l2output')
l2pipeline.connect([(l2source,onesamplettestdes,[('outfiles','in_files')]),
                  (onesamplettestdes,l2estimate,[('spm_mat_file','spm_mat_file')]),
                  (l2estimate,l2conestimate,[('spm_mat_file','spm_mat_file'),
                                             ('beta_images','beta_images'),
                                             ('residual_image','residual_image')]),
                    ])
                    
if __name__ == '__main__':
    l2pipeline.run('MultiProc')