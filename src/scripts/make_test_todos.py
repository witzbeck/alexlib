from pathlib import Path

from alexlib.core import to_clipboard
from alexlib.files import Directory, File
from alexlib.ml.llm_response import MarkdownResponse, TestCaseResponse
from alexlib.times import Timer

PY_FILE_PATTERN = "files"
MODULE_PATH = Path(__file__).parent
TESTS_PATH = MODULE_PATH.parent / "tests"

MODULE_DIR = Directory.from_path(MODULE_PATH)
TESTS_DIR = Directory.from_path(TESTS_PATH)


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


def get_test_case_files_from_py_files(py_files: list[File]) -> list[File]:
    """Get the test cases for all python files in a directory."""
    ret = [
        File.from_path(file.path.parent / f"{file.path.stem}_test_cases.md")
        for file in py_files
    ]
    return [file for file in ret if file.path.exists()]


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


def get_responses_from_files(
    files: list[File],
) -> list[MarkdownResponse]:
    """Get the test case responses for markdown files in a directory."""
    return [MarkdownResponse.from_file(file) for file in files]


def mk_llm_test_request(
    pyfile: File,
    testcase_response: TestCaseResponse,
) -> str:
    for heading, cases in testcase_response.heading_step_map.items():
        parent_name, stem = pyfile.path.parent.name, pyfile.path.stem
        module_name = stem if parent_name == "alexlib" else f"{parent_name}.{stem}"
        heading = (
            "".join([x for x in heading if x.isalpha() or x in " _"])
            .replace(" ", "_")
            .strip("_")
            .lower()
        )
        steps = "\n".join(cases)
        pytest_filename = f"test_{pyfile.path.stem}_{heading}.py"
        pytest_filepath = TESTS_PATH / pytest_filename
        if pytest_filepath.exists():
            if len(pytest_filepath.read_text().split("\n")) < 10:
                pytest_filepath.unlink()
        if not pytest_filepath.exists():
            pytest_filepath.touch(exist_ok=True)
            tocopy = "\n".join(
                [
                    f"""Write comprehensive and detailed implementations of the test cases
                    for the supplied code using the unittest framework.
                    Please use explicit imports and avoid wildcard imports.
                    Please include a docstring for each function, class, and the module.
                    The module name is 'alexlib.{module_name}'.\n""",
                    f"Test cases for {heading}:\n",
                    steps,
                    f"Here's the module text:\n\n{pyfile.text}\n",
                ]
            )
            to_clipboard(tocopy)
            input(
                f"\nPaste the returned tests into {pytest_filepath.name}, then press enter.\n"
            )


if __name__ == "__main__":
    t = Timer()
    py_files = get_python_files(MODULE_DIR, allchildren=True)
    py_files = [file for file in py_files if PY_FILE_PATTERN in file.name]
    ncases_total, nsteps_total = 0, 0
    for pyfile in py_files:
        tcfile = File.from_path(
            pyfile.path.parent / f"{pyfile.path.stem}_test_cases.md"
        )
        if not tcfile.path.exists():
            continue
        resp = TestCaseResponse.from_file(tcfile)
        mk_llm_test_request(pyfile, resp)
        ncases = len(resp.heading_step_map)
        nsteps = len(resp.step_indices)
        ncases_total += ncases
        nsteps_total += nsteps
        print(tcfile, f"has {ncases} cases and {nsteps} steps.")
    print("Total number of cases:", ncases_total)
    print("Total number of steps:", nsteps_total)
    t.log_from_start()
