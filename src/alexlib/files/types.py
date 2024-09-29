from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union


@dataclass(frozen=True)
class CommentSyntax:
    line_comment: Optional[Union[str, List[str]]]
    multiline_comment: Optional[Tuple[str, str]]


c_comment_syntax = CommentSyntax("//", ("/*", "*/"))
perl_comment_syntax = CommentSyntax("#", ("=begin", "=cut"))
html_comment_syntax = CommentSyntax(None, ("<!--", "-->"))
sql_comment_syntax = CommentSyntax("--", ("/*", "*/"))
shell_comment_syntax = CommentSyntax("#", None)
ps1_comment_syntax = CommentSyntax("#", ("<#", "#>"))
python_comment_syntax = CommentSyntax("#", ('"""', '"""'))
css_comment_syntax = CommentSyntax(None, ("/*", "*/"))
ini_comment_syntax = CommentSyntax([";", "#"], None)
tex_comment_syntax = CommentSyntax("%", None)
yaml_comment_syntax = CommentSyntax("#", None)
json_comment_syntax = CommentSyntax("//", None)
toml_comment_syntax = CommentSyntax("#", None)


@dataclass(frozen=True)
class FileType:
    """the type of a file and related attributes"""

    name: str
    suffix: str
    comment_syntax: CommentSyntax = field(default=None)

    def __repr__(self) -> str:
        toshow = self.name if self.name is not None else self.suffix
        return f"{self.__class__.__name__}({toshow})"

    @classmethod
    def from_suffix(self, suffix: str, mapping: dict) -> "FileType":
        """creates a FileType from a suffix"""
        return mapping[suffix]


yaml_filetype = FileType("YAML", ".yaml", shell_comment_syntax)
json_filetype = FileType("JSON", ".json", shell_comment_syntax)
toml_filetype = FileType("TOML", ".toml", shell_comment_syntax)
tex_filetype = FileType("LaTeX", ".tex", CommentSyntax("%", None))
shell_filetype = FileType("Shell", ".sh", shell_comment_syntax)
batch_filetype = FileType("Batch", ".bat", CommentSyntax("rem", None))
ini_filetype = FileType("INI", ".ini", CommentSyntax([";", "#"], None))
md_filetype = FileType("Markdown", ".md", html_comment_syntax)
html_filetype = FileType("HTML", ".html", html_comment_syntax)
css_filetype = FileType("CSS", ".css", CommentSyntax(None, ("/*", "*/")))
sql_filetype = FileType("SQL", ".sql", sql_comment_syntax)
r_filetype = FileType("R", ".R", shell_comment_syntax)
rmd_filetype = FileType("R Markdown", ".Rmd", shell_comment_syntax)
ipynb_filetype = FileType("Jupyter Notebook", ".ipynb", shell_comment_syntax)
rb_filetype = FileType("Ruby", ".rb", perl_comment_syntax)
py_filetype = FileType("Python", ".py", python_comment_syntax)
ps1_filetype = FileType("PowerShell", ".ps1", ps1_comment_syntax)
pl_filetype = FileType("Perl", ".pl", perl_comment_syntax)
ts_filetype = FileType("TypeScript", ".ts", c_comment_syntax)
js_filetype = FileType("JavaScript", ".js", c_comment_syntax)
java_filetype = FileType("Java", ".java", c_comment_syntax)
cs_filetype = FileType("C#", ".cs", c_comment_syntax)
cpp_filetype = FileType("C++", ".cpp", c_comment_syntax)

SUFFIX_FILETYPE_MAP = {
    ".yaml": yaml_filetype,
    ".yml": yaml_filetype,
    ".json": json_filetype,
    ".toml": toml_filetype,
    ".tex": tex_filetype,
    ".sh": shell_filetype,
    ".bat": batch_filetype,
    ".ini": ini_filetype,
    ".md": md_filetype,
    ".html": html_filetype,
    ".css": css_filetype,
    ".sql": sql_filetype,
    ".R": r_filetype,
    ".Rmd": rmd_filetype,
    ".ipynb": ipynb_filetype,
    ".rb": rb_filetype,
    ".py": py_filetype,
    ".ps1": ps1_filetype,
    ".pl": pl_filetype,
    ".ts": ts_filetype,
    ".js": js_filetype,
    ".java": java_filetype,
    ".cs": cs_filetype,
    ".cpp": cpp_filetype,
}
