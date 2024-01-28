from pathlib import Path

from alexlib.files import Directory, File
from alexlib.ml.llm_response import MarkdownResponse
from alexlib.times import Timer

MODULE_DIR = Directory.from_path(Path(__file__).parent)


def get_single_file_test_cases(py_file: File) -> str:
    """Get the test cases for a given python file."""
    py_file.text_to_clipboard(
        toprepend="create a comprehensive set of test cases for this file.\n\n"
    )
    test_filename = f"{py_file.path.stem}_test_cases.md"
    test_filepath = py_file.path.parent / test_filename
    if test_filepath.exists():
        print(f"{test_filepath} already exists. Skipping.\n")
        return
    test_filepath.touch(exist_ok=True)
    print(
        f"We've copied the text of {py_file} to the clipboard and created {test_filename}."
    )
    generated_cases = input(
        "Paste the generated test cases into the empty file, then press enter.\n"
    )
    return generated_cases


def get_python_files(directory: Directory, allchildren: bool = False) -> list[File]:
    """Get the python files in a directory."""
    return [
        file
        for file in directory.get_type_filelist(".py", allchildren=allchildren)
        if file.name != "__init__.py"
    ]


def get_test_case_files(directory: Directory, allchildren: bool = False) -> list[File]:
    """Get the test cases for all python files in a directory."""
    filelist = directory.allchildfiles if allchildren else directory.filelist
    return [file for file in filelist if "_test_cases" in file.name]


def get_test_cases_loop(directory: Directory, allchildren: bool = False) -> None:
    """Loops through all python and test_cases files in a directory
    - allows for efficient utilization of an LLM for test case generation."""
    py_files = get_python_files(directory, allchildren=allchildren)
    md_files = get_test_case_files(directory, allchildren=allchildren)
    for md_file in md_files:
        if md_file.nlines <= 10:
            print(f"{md_file} has too few lines. Deleting.\n")
            md_file.rm()

    for py_file in py_files:
        _ = get_single_file_test_cases(py_file)


def get_responses_from_files(files: list[File]) -> list[MarkdownResponse]:
    """Get the test case responses for markdown files in a directory."""
    return [MarkdownResponse.from_file(file) for file in files]


if __name__ == "__main__":
    t = Timer()
    testcase_files = get_test_case_files(MODULE_DIR, allchildren=True)
    testcases_responses = get_responses_from_files(testcase_files)
    ncases_total, nsteps_total = 0, 0
    for file, resp in zip(testcase_files, testcases_responses):
        ncases = len(resp.heading_step_index_map)
        nsteps = len(resp.step_indices)
        ncases_total += ncases
        nsteps_total += nsteps
        print(file, f"has {ncases} cases and {nsteps} steps.")
    print("\nNumber of files:", len(testcase_files))
    print("Total number of cases:", ncases_total)
    print("Total number of steps:", nsteps_total)
    t.log_from_start()
