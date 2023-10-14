# DICOM Import Repair

This package provides scripts for repairing DICOM headers when errors are
encountered importing into Eclipse.

## Requirements

### Required Packages

- pydicom=2.3.1
- PySimpleGUI=4.60.4
- Python>=3.9.13

### Recommended DEV Packages

(_Used to run the included Jupyter Notebooks_)

- pandas
- xlwings
- jupyterlab

## Source Files

- dicom_repair_tools
Key Functions:
  - scan_dicom_images
  - count_repairs
  - perform_repairs

- dicom_repair_functions
Key Functions:
  - REPAIR_METHODS

- dicom_repair_gui
Key Functions:
  - make_window
  - get_file_paths
  - status_output
  - wait_for_acknowledgement
