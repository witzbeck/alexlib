from pathlib import Path

from alexlib.files import Directory, File


def get_test_cases(py_file: File) -> str:
    """Get the test cases for a given python file."""
    py_file.text_to_clipboard(
        toprepend="create a comprehensive set of test cases for this file.\n\n"
    )
    test_filename = f"{py_file.path.stem}_test_cases.md"
    test_filepath = py_file.path.parent / test_filename
    test_filepath.touch()
    print(
        f"We've copied the text of {py_file} to the clipboard and created {test_filename}."
    )
    generated_cases = input(
        "Paste the generated test cases to the file, then press enter."
    )
    return generated_cases


if __name__ == "__main__":
    module_ = Directory.from_path(Path(__file__).parent)
    py_files = module_.get_type_filelist(".py")
    md_files = module_.get_type_filelist(".md")
    for md_file in md_files:
        if md_file.nlines <= 10:
            md_file.rm()

    for py_file in py_files:
        if py_file.name == "__init__.py":
            continue
        test_filepath = py_file.path.parent / f"{py_file.path.stem}_test_cases.md"
        if test_filepath.exists():
            print(f"{test_filepath} already exists. Skipping.\n")
            continue
        generated_cases = get_test_cases(py_file)
        print(f"We've written the test cases to {test_filepath}.\n")
