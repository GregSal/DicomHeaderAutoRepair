'''Primary interface for running the DICOM repair.'''
# %% Imports
from pathlib import Path
from typing import Any, Dict, List

import PySimpleGUI as sg

# %% GUI Progress bar class
class ProgressBar(sg.ProgressBar):
    '''A progress bar that tracks it's own progress.
    '''
    def __init__(self, *args, value=0, **kwargs):
        '''Generate the progress bar and add the starting value.
        Args:
            value (int, optional): The starting value for the progress bar.
                Defaults to 0.
        '''
        super().__init__(*args, **kwargs)
        self.value = value

    def update(self, *args, **kwargs)->bool:
        '''Update the progress bar and set the current value, if it is given.

        Returns:
            bool: Returns True if update was OK. False means something wrong
                with window or it was closed.
        '''
        status = super().update(*args, **kwargs)
        # if current_count is given, update the value attribute.
        if 'current_count' in kwargs:
            current_count = kwargs['current_count']
        elif len(args) > 0:
            current_count = args[0]
        else:
            current_count = None
        if current_count is not None:
            self.value = current_count
        return status

    def increment(self, step_size=1):
        '''Increase the progress bar value by step_size.

        Args:
            step_size (int): the amount to increment the progress level by.

        Returns:
            bool: Returns True if update was OK. False means something wrong
                with window or it was closed.
        '''
        current_level = self.value
        if not current_level:
            current_level = 0
        new_level = current_level + step_size
        status = self.update(new_level)
        return status


# %%  Setup functions
# Functions to build directory selectors
def file_selector(selection: str, file_k: str, frame_title: str,
                    starting_path=Path.cwd(), file_type=None)->sg.Frame:
    '''Generate a file selector widget set.

    Args:
        selection (str): File selection type.  One of:
            - 'read file'
            - 'save file'
            - 'read files'
            - 'dir'
        file_k (str): Output reference tag for the file or directory selection.
        frame_title (str): Label to place above the selection widget
        starting_path (Path, str, optional): Starting path for the file
            selection. Defaults to Path.cwd().
        file_type (List[str], optional): List of possible file tpe extensions.
            Defaults to None.

    Raises:
        ValueError: If selection is not supplied a valid option.

    Returns:
        sg.Frame: A widget set to be inserted into a indow layout.
    '''
    # Check all starting path possibilities
    if isinstance(starting_path, str):
        starting_path = Path(starting_path)
    if starting_path.exists():
        if starting_path.is_file():
            initial_file = starting_path.name
            initial_dir = starting_path.parent
        elif starting_path.is_dir():
            initial_dir = str(starting_path)
            initial_file = ''
    else:
        if not starting_path.parent.exists():
            starting_path = Path.cwd()
            initial_dir = str(starting_path)
            initial_file = ''
        else:
            initial_dir = starting_path.parent
            initial_file = ''

    # Set browser by selection type
    if 'read file' in selection:
        browse = sg.FileBrowse(initial_folder=initial_dir,
                                file_types=file_type)
        initial_text = initial_file
    elif 'save file' in selection:
        browse = sg.FileSaveAs(initial_folder=initial_dir,
                                file_types=file_type)
        initial_text = initial_file
    elif 'read files' in selection:
        browse = sg.FilesBrowse(initial_folder=initial_dir,
                                file_types=file_type)
        initial_text = initial_file
    elif 'dir' in selection:
        browse = sg.FolderBrowse(initial_folder=initial_dir)
        initial_text = initial_dir
    else:
        raise ValueError(f'{selection} is not a valid browser type')

    # Build the selector group
    file_selector_frame = sg.Frame(title=frame_title, layout=[
        [sg.InputText(key=file_k, default_text=initial_text, size=(90, 1)),
         browse]])

    return file_selector_frame


def make_file_selection_frame(starting_input_path: Path,
                              starting_output_path: Path)->sg.Frame:
    '''Define the directories to be selected.'''
    # Select Input Directory
    input_title = 'Select the directory containing DICOM files to be repaired.'
    input_path_def = dict(frame_title=input_title, file_k='input_folder',
                        selection='dir', starting_path=starting_input_path)
    input_path_selector = file_selector(**input_path_def)

    # Select Output Directory
    output_title = ''.join(['Select the directory where repaired DICOM files',
                            'will be saved.'])
    output_path_def = dict(frame_title=output_title, file_k='output_folder',
                        selection='dir',starting_path=starting_output_path)
    output_path_selector = file_selector(**output_path_def)

    # Should Sub-Directories be included?
    help_text = ''.join(['Iteratively search all subdirectories of the ',
                        'supplied directory for DICOM files'])
    include_sub_dir_check = sg.Checkbox('Include Sub-Directories?',
                                        tooltip=help_text, default=True,
                                        key='include_sub_dir',expand_x = True)
    # Widget layout
    path_selection_layout=[
        [input_path_selector],
        [include_sub_dir_check],
        [output_path_selector]]

    # Build the frame
    path_frame = sg.Frame(key='Dir Selection',
                        title='Directories',
                        title_location=sg.TITLE_LOCATION_TOP_LEFT,
                        layout=path_selection_layout)
    return path_frame


# %% GUI functional groups
# Function to make buttons
def make_actions_buttons()->sg.Column:
    '''Define the action buttons.'''
    help_text = 'Begin repairing DICOM files.'
    start_button = sg.Button(button_text='Repair', key='Repair',
                             tooltip=help_text, button_color='blue',
                             disabled_button_color = None,
                             highlight_colors = None,
                             mouseover_colors = (None, None),
                             font = None,
                             size = (None, None), pad = None,
                             border_width = None, auto_size_button = None,
                             disabled = False, visible = True)
    actions_list = sg.Column([[start_button, sg.Quit(button_color='red')]])
    return actions_list


# Functions to track progress
def make_status_frame()->sg.Frame:
    '''Build the status reporting widget set.'''
    status_layout=[
        [sg.Multiline(key='Status', autoscroll=True,
                      size=(97,10), pad=(10,10))],
        [ProgressBar(max_value=100, orientation='h', bar_color=('cyan', 'white'),
                     size=(62, 30), pad=(10,10), key='Progress')]
        ]
    status_frame = sg.Frame(title='Status',
                            title_location=sg.TITLE_LOCATION_TOP,
                            layout=status_layout)
    return status_frame


# Status reporting function
def print_to_window(main_window: sg.Window, status_element: sg.Element, text: str):
    '''Status reporting function framework.

    Args:
        main_window (sg.Window): Window containing the widget.
        status_element (sg.Element): The widget element.
        text (str): The text to add to the status.
    '''
    status_element.print(text, text_color=None, background_color=None)
    main_window.refresh()


def status_output(message, value: int = None, max_count: int = None,
                  repair_log: List[str] = None,
                  main_window: sg.Window = None,
                  status_element: sg.Element = None,
                  progress_element: sg.Element = None):
    '''Sends message to status widget and updates progress bar as needed.

    This function is intended to be used with partial to set the repair_log,
    window and elements.

    Args:
        message (str, optional): The new repair log message. If the string is
            empty, status and repair_log will not be updated. Defaults to an
            empty string.
        value (int, optional): A specific progress level to be set. If supplied,
            the progress level will be modified to the given value regardless of
            previous values. Defaults to None.
        max_count (int, optional): The maximum (100%) progress level. If
            supplied, the maximum progress level will be set to this value and
            the progress level will be reset to 0. Defaults to None.
        repair_log (List[str]): A list of all repair log messages.  Used for
            stats analysis.
        main_window (sg.Window): Window containing the status and
            progress bar widgets.
        status_element (sg.Element): The status widget element object.
        progress_element (sg.Element): The progress bar widget element object.
    '''
    if max_count:
        progress_element.update(0, max=max_count)
    if value:
        progress_element.update(value)
    if message:
        status_element.print(message, text_color=None, background_color=None)
        repair_log.append(message)
        if 'Checking file' in message:
            progress_element.increment()
    main_window.refresh()


# %%  Main window function
def make_window(starting_input_path: Path, starting_output_path: Path):
    '''This blocks out the main sections of the GUI.

    Returns:
        sg.Window: The main GUI window.
    '''
    path_frame = make_file_selection_frame(starting_input_path,
                                           starting_output_path)
    actions_group = make_actions_buttons()
    status_frame = make_status_frame()

    main_layout = [
        [path_frame],
        [actions_group],
        [status_frame]
        ]

    window = sg.Window('DICOM Repair', finalize=True, resizable=True,
                       layout=main_layout)
    return window


def get_file_paths(window: sg.Window)->Dict[str,Any]:
    '''Call the main window to get directory paths.

    Args:
        window (sg.Window): Window containing the action buttons.

    Returns:
        Dict[str,Any]: Parameter values from the GUI window, with an additional
            item 'process_repairs', which is True if the 'Repair' button was
            pressed.
    '''
    # Get file paths
    process_repairs = True
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            process_repairs = False
            window.close()
            break
        if event == 'Quit':
            process_repairs = False
            window.close()
            break
        if event == 'Repair':
            break
    values['process_repairs'] = process_repairs
    return values


def wait_for_acknowledgement(window: sg.Window):
    '''Pause the main window until closed.

    Args:
        window (sg.Window): Window containing the action buttons.
    '''
    window['Repair'].update(disabled=True)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == 'Quit':
            break
        if event == 'start_repair':
            break
    window.close()


# %% Main
def main():
    '''Testing'''
    #data_path = Path.cwd() / 'DICOM Test Data'
    output_path = Path.cwd() / 'Output'
    test_data_path = Path(r'W:\Python Projects\DICOM Repair\DICOM Test Data\Invalid^Characters [Error3]\Series 012 [PT - MAC]')

    window = make_window(starting_input_path=test_data_path,
                         starting_output_path=output_path)

    window.Refresh()
    # Run the window
    while True:
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED:
            break
        if event == 'Quit':
            break
        if event == 'Repair':
            break
        print(values)

    window.close()

if __name__ == '__main__':
    main()
