'''Functions for repairing specific DICOM import issues.
These functions perform the testing and repair of the DICOM metadata.
Each function tests and repairs a different import problem.

All of the functions have the same set of arguments:
    dataset (pydicom.Dataset): The pydicom.Dataset read from a DICOM file by the
        pydicom module.
    status_output (Callable): A function taking one string parameter.  This
        function is used for reporting/logging the results of the repair
        attempt.

The do_repairs function


    Args:
        input_path (Path): Path to the directory containing DICOM files.
        output_path (Path): Path to the directory where the repaired DICOM
            files will be stored.
        status_output (Callable): A function taking one string parameter.
            Passed to each of the repair_methods. Used for reporting the
            results of the repair.
'''
# %% Imports
from typing import Callable
from pathlib import Path

import pydicom

from dicom_repair_tools import perform_repairs, count_repairs


# %% Repair Functions
# Repair Invalid Character
def fix_invalid_characters(dataset: pydicom.Dataset,
                           status_output: Callable)->pydicom.Dataset:
    '''Identify and remove certain elements containing invalid characters.

    Two DICOM elements are checked for invalid characters:
    - "Body Part Examined" (0018, 0015)
    - "Other Patient IDs" (0010, 1000)

    Invalid characters are identified by the element's value beginning with
    a "/", which is the beginning of a escape sequence for non-printable text.
    Elements values containing invalid characters are replaced with blank
    text "".

    Args:
        dataset (pydicom.Dataset): The full DICOM dataset.
        status_output (Callable): Function for reporting the results of the
            repair attempt.

    Returns:
        pydicom.Dataset: The DICOM dataset with any repairs made.
    '''
    data_elements = ['BodyPartExamined', 'OtherPatientIDs']
    message_format = ''.join([
        'Invalid Character found in element {name}.',
        '\tReplaced with blank string.'
        ])
    for element_name in data_elements:
        if element_name in dataset:
            data_element = dataset.data_element(element_name)
            try:
                invalid_char = data_element.value.startswith(r'/')
            except AttributeError:
                pass
            else:
                if invalid_char:
                    message = message_format.format(name=element_name)
                    status_output(message)
                    data_element.value = ''
    return dataset


#  Repair Incorrect Modality
def fix_incorrect_modality(dataset: pydicom.Dataset,
                           status_output: Callable)->pydicom.Dataset:
    '''Check that the image modality element matches the actual image type.

    The DICOM "Modality" element (0008, 0060) must be “CT” for CT images and
    "PT" for PET images.  The image type is identified using surrogate elements
    that contain image parameters unique to that particular image type. CT
    images are identified by the presence of the "KVP" (0018, 0060) element.
    PET images are identified by the presence of the
    "Radiopharmaceutical Information Sequence" (0054, 0016) element.

    If the image type does not match with the modality value it is corrected.

    Args:
        dataset (pydicom.Dataset): The full DICOM dataset.
        status_output (Callable): Function for reporting the results of the
            repair attempt.

    Returns:
        pydicom.Dataset: The DICOM dataset with any repairs made, or None if
            the DICOM dataset does not contain the "Modality" element.
    '''
    message_format = ''.join([
        'Incorrect Modality found.',
        '\tModality changed from "{old_modality}" to "{new_modality}"'
        ])

    # if 'Modality' element is not present the DICOM data set is invalid.
    if 'Modality' not in dataset:
        message = 'Modality element not found. File not used.'
        status_output(message)
        dataset = None
    else:
        # CHeck modality set against image type
        modality = dataset.data_element('Modality').value
        # Identify CT images
        if 'KVP' in dataset:
            if 'CT' not in modality:
                message = message_format.format(old_modality=modality,
                                                new_modality='CT')
                status_output(message)
                dataset.data_element('Modality').value = 'CT'

        # Identify PET images
        if 'RadiopharmaceuticalInformationSequence' in dataset:
            if 'PT' not in modality:
                message = message_format.format(old_modality=modality,
                                                new_modality='PT')
                status_output(message)
                dataset.data_element('Modality').value = 'PT'

    return dataset


# Repair Mismatched Addresses
def fix_incorrect_address(dataset: pydicom.Dataset,
                           status_output: Callable)->pydicom.Dataset:
    '''Repair suspected mismatched institution addresses.

    Eclipse requires that the DICOM "InstitutionAddress" element (0008, 0081)
    be the same for all images (CT and PET) in the same study.  From our
    experience, this problem only occurs with PET-CTs coming from "Mississauga"
    or from "University Health Network".  For the sake of speed, we do not
    compare the PET and CT addresses.  Since "Institution Address" is not a
    critical piece of information, any time the "Institution Address" contains
    "Mississauga" or "University Health Network" it is set to a blank string.

    Update July 12 2023:
    This problem is now also occurring with MR images from KGH. Added
    `'Stuart 76,Kingston' in address` ad an additional possible condition for
    removing the address.

    Args:
        dataset (pydicom.Dataset): The full DICOM dataset.
        status_output (Callable): Function for reporting the results of the
            repair attempt.

    Returns:
        pydicom.Dataset: The DICOM dataset with any repairs made.
    '''
    message_format = ''.join([
        'Mismatched Institution Addresses Suspected.',
        '\tAddress: "{address}"',
        ' Replaced with blank string.'
        ])
    if 'InstitutionAddress' in dataset:
        address = dataset.data_element('InstitutionAddress').value
        institution = dataset.data_element('InstitutionName').value
        if (('Mississauga' in address) |
            ('Stuart 76,Kingston' in address) |
            ('University Health Network' in institution)):
            # Find the first space after 20 characters to create a shortened
            # version of the address.
            address_break = address.find(' ',25)
            short_address = address[:address_break]
            message = message_format.format(address=short_address)
            status_output(message)
            dataset.data_element('InstitutionAddress').value = ''
    return dataset


# %% Active Repair Functions
# This is a list of all currently active repair functions
REPAIR_METHODS = [
        fix_invalid_characters,
        fix_incorrect_modality,
        fix_incorrect_address
        ]


# %% Main
def main():
    '''Demo method.'''
    repair_log = []

    def status_output(message):
        '''Record and print repair messages.
        Args:
            message (str): Repair message.
        '''
        repair_log.append(message)
        #print(message)

    data_path = Path.cwd() / 'DICOM Test Data'
    data_path = Path.cwd() /  r'DICOM Test Data\Invalid^Characters [Error3]\Series 012 [PT - MAC]'
    output_path = Path.cwd() / 'Output'
    perform_repairs(data_path, output_path, REPAIR_METHODS, status_output)
    print(count_repairs(repair_log))

if __name__ == '__main__':
    main()
