'''

'''

Acknowledgement_UoE = '''rule begin
obligation acknowledge source OnImport.
attribute source [UoE].
end
'''

Acknowledgement_R = '''rule begin
obligation acknowledge source OnImport.
attribute source [Rui].
end
'''


Remove_Source_UoE = '''[
Propagate("arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/processfiles_2/cyclone_workflow", ["arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/processfiles_2/output"]),
Delete(match_value="UoE"),
]
'''

Change_Source_UoE_UK = '''[
Propagate("arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/processfiles_3/cyclone_workflow", ["arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/processfiles_3/output"]),
Edit("str", "UK", match_value="UoE"),
]
'''
