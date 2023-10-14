xcopy ".\*.py" ".\For Distribution" /V /Y
del ".\For Distribution\__init__.py"
xcopy ".\For Distribution\*.*" "M:\DICOM_IMPORT\DICOM_Import_Repair" /F /V /S /Y
xcopy ".\Environment\DICOM_Repair_specfile.txt" "M:\DICOM_IMPORT\DICOM_Import_Repair\install dicom_repair" /V /Y
