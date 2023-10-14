'''Main DICOM Repair Method.'''
# %% Imports
from pathlib import Path
from functools import partial

from dicom_repair_tools import scan_dicom_images, count_repairs
from dicom_repair_tools import perform_repairs
from dicom_repair_functions import REPAIR_METHODS

from dicom_repair_gui import make_window, get_file_paths, status_output
from dicom_repair_gui import wait_for_acknowledgement

# %% Default Paths
INPUT_PATH = r'\\dkphysicspv1\Radiation_Therapy\DICOM_IMPORT\MicroDicom'
OUTPUT_PATH = r'\\dkphysicspv1\Radiation_Therapy\DICOM_IMPORT\Import Repair\repaired'


# %% Main
def main():
    '''Primary function for running DICOM repairs.'''
    # Build the GUI
    window = make_window(starting_input_path=INPUT_PATH,
                         starting_output_path=OUTPUT_PATH)
    repair_log = []
    status_update = partial(status_output, main_window=window,
                            status_element=window['Status'],
                            progress_element=window['Progress'],
                            repair_log=repair_log)

    # Select directory paths
    values = get_file_paths(window)
    if not values['process_repairs']:
        return  # Exit if 'Repair' not clicked.
    input_path = Path(values['input_folder'])
    output_path = Path(values['output_folder'])
    include_subdirectories = values['include_sub_dir']

    # Initialize status
    file_gen = scan_dicom_images(input_path, include_subdirectories)
    number_of_files = len([f for f in file_gen])
    status_update(message=f'Found {number_of_files} files',
                  max_count=number_of_files)

    # Do the repairs
    perform_repairs(input_path, output_path, REPAIR_METHODS, status_update)

    summary_text = count_repairs(repair_log)
    status_update(message=summary_text)
    wait_for_acknowledgement(window)


if __name__ == '__main__':
    main()
