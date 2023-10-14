call Miniconda3-latest-Windows-x86_64.exe /s /InstallationType=AllUsers /RegisterPython=1 /D=C:\ProgramData\Miniconda3
call C:\ProgramData\Miniconda3\Scripts\activate.bat C:\ProgramData\Miniconda3
call conda config --append channels conda-forge
call conda create --name DICOM_Repair --file DICOM_Repair_specfile.txt
call conda activate DICOM_Repair 
