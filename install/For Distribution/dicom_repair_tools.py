'''Functions used to inspect and repair errors in DICOM metadata that prevent
Eclipse Importing.
'''
# %% Imports
from typing import List, Iterable, Callable
from pathlib import Path
from collections import Counter

import pydicom


#%% Status reporting functions
def count_repairs(repair_log: List[str])->str:
    '''Summarize the repair actions

    Args:
        repair_log (List[str]): The output from the DICOM repair functions.

    Returns:
        str: A summary of the repair actions taken
    '''
    def clean_log(repair_log: List[str])->str:
        for text in repair_log:
            if text.startswith('Checking file'):
                yield 'Checking file'
            elif text.startswith('Found '):
                continue
            else:
                new_text = text.replace('\r', ' ')
                new_text = new_text.replace('\n', ' ')
                yield new_text

    def repair_summary(log, num):
        if 'Checking file' in log:
            return ''
        log_split = log.split('\t', 1)
        if len(log_split) == 2:
            found, action = log_split
        else:
            found = log
            action = ''
        repair_text = f'\tIn {num} files, \n\t\t{found}\n\t\t{action}'
        return repair_text

    stats_log = [line for line in clean_log(repair_log)]
    stats = Counter(stats_log)
    file_count = stats.pop('Checking file', 0)
    summary_text_lines = [
        '',
        '********  DICOM File Repair Completed  ********',
        f'\nNumber of files analyzed:\t{file_count:d}',
        'Repairs Made:']
    action_summaries = [repair_summary(log, num) for log, num in stats.items()]
    summary_text_lines.extend(action_summaries)
    summary_text = '\n'.join(summary_text_lines)
    return summary_text


# %%  Utility Functions
# These functions manage the File io etc.

# Read the DICOM file.
def load_header(file_path: Path, status_output: Callable)->pydicom.Dataset:
    '''Load DICOM meta data from a given file.

    Args:
        file_path (Path): Path to the DICOM file.

    Returns:
        pydicom.Dataset: The full dataset read from the DICOM file. If the file
            does not contain valid DICOM data, returns None.
    '''
    try:
        dataset = pydicom.dcmread(file_path)
    except pydicom.errors.InvalidDicomError:
        message = f'{file_path.name} did not contain valid DICOM data.  Skipped.'
        status_output(message)
        dataset = None

    return dataset


# Scan a directory of DICOM files, yielding the DICOM datasets.
def scan_dicom_images(data_path: Path,
                      include_subdirectories=True)->Iterable[Path]:
    '''Create a generator of DICOM files in a given directory.

    Args:
        file_path (Path): Path to the directory containing DICOM files.
        include_subdirectories (bool) If True subdirectories of the supplied
            directory will also be scanned.

    Returns:
        Generator[Path]: A generator of the files within a given directory.
    '''
    if include_subdirectories:
        scan_pattern = '**/*'
    else:
        scan_pattern = '*.*'
    return data_path.glob(scan_pattern)


def get_dicom_images(data_path: Path,
                     status_output=print,
                     include_subdirectories=True)->pydicom.Dataset:
    '''Yield DICOM meta data for each file in a given directory.

    Args:
        file_path (Path): Path to the directory containing DICOM files.
        status_output (Callable): A function taking one string parameter.  Used
            for reporting the results of the trying to load the DICOM file.
        include_subdirectories (bool) If True subdirectories of the supplied
            directory will also be scanned.

    Yields:
        pydicom.Dataset: The full dataset read from the DICOM file. If the file
            does not contain valid DICOM data, returns None.
    '''
    file_gen = scan_dicom_images(data_path, include_subdirectories)
    for dicom_file in file_gen:
        if dicom_file.is_file():
            message = f'Checking file {dicom_file.name}'
            status_output(message)
            dataset = load_header(dicom_file, status_output)
            if dataset:
                yield dataset


# Generate a DICOM filename.
def build_dicom_file_name(dataset: pydicom.Dataset)->str:
    '''Generate a filename for a given DICOM dataset.

    The filename consists of the DICOM modality, the Instance UID and the
    '.dcm' extension.

    Args:
        dataset (pydicom.Dataset): The DICOM dataset requiring a corresponding
            file name.

    Returns:
        str: A filename based on the information in the DICOM dataset.
    '''
    modality = dataset.data_element('Modality').value
    instance_uid = dataset.data_element('SOPInstanceUID').value
    file_name = ''.join([
        modality,
        instance_uid,
        '.dcm'
        ])
    return file_name


# Save a DICOM file
def save_dicom_dataset(dataset: pydicom.Dataset, output_path: Path):
    '''Save a DICOM file with a name based on the information in the dataset.

    Args:
        dataset (pydicom.Dataset): The DICOM dataset to be saved.
        output_path (Path): Path to the directory where the DICOM dataset
            will be saved.
    '''
    output_file_name = build_dicom_file_name(dataset)
    output_file_path = output_path / output_file_name
    dataset.save_as(output_file_path)


# Apply Repair Functions
def perform_repairs(input_path: Path, output_path: Path,
                    repair_methods: List[Callable],
                    status_output: Callable):
    '''Identify and apply necessary DICOM metadata repairs.

    Iterate through each DICOM file in the `input_path` folder.  Apply any
    necessary repairs and save the results DICOM dataset in the directory
    specified by `output_path`.  Invalid DICOM files will not be saved and
    directory structure is not maintained.

    Args:
        input_path (Path): Path to the directory containing DICOM files.
        output_path (Path): Path to the directory where the repaired DICOM
            files will be stored.
        repair_methods (List[Callable]): DICOM dataset repair functions.  The
            function must take the following parameters:
            - dataset (pydicom.Dataset): The DICOM dataset to be repaired.
            - status_output (Callable): A function taking one string parameter,
                used for reporting the results of the repair.
        status_output (Callable): A function taking one string parameter.
            Passed to each of the repair_methods. Used for reporting the
            results of the repair.
    '''
    for dataset in get_dicom_images(input_path, status_output):
        # Apply all repair methods to the dataset
        for repair_method in repair_methods:
            dataset = repair_method(dataset, status_output)
        # Save the repaired dataset as a DICOM file
        if dataset:
            save_dicom_dataset(dataset, output_path)
