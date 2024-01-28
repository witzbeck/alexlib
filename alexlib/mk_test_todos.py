from pathlib import Path

from alexlib.files import Directory, File


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


def get_existing_test_cases(
    directory: Directory, allchildren: bool = False
) -> list[File]:
    """Get the test cases for all python files in a directory."""
    filelist = directory.allchildfiles if allchildren else directory.filelist
    return [file for file in filelist if "_test_cases" in file.name]


def get_test_cases_loop(directory: Directory, allchildren: bool = False) -> None:
    """Loops through all python and test_cases files in a directory
    - allows for efficient utilization of an LLM for test case generation."""
    py_files = get_python_files(directory, allchildren=allchildren)
    md_files = get_existing_test_cases(directory, allchildren=allchildren)
    for md_file in md_files:
        if md_file.nlines <= 10:
            print(f"{md_file} has too few lines. Deleting.\n")
            md_file.rm()

    for py_file in py_files:
        _ = get_single_file_test_cases(py_file)


if __name__ == "__main__":
    module_ = Directory.from_path(Path(__file__).parent)
    testcase_files = get_existing_test_cases(module_, allchildren=True)
    for testcase_file in testcase_files:
        print(testcase_file)
