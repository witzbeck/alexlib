from pytest import fixture

from alexlib.files.pdfs import Font


@fixture(scope="module")
def font():
    return Font()


def test_font_is_font(font: Font):
    assert isinstance(font, Font)


def test_font_has_name(font: Font):
    assert font.name


def test_font_has_size(font: Font):
    assert font.size


def test_font_as_tuple(font: Font):
    assert isinstance(tuple(font), tuple)


def test_font_ps_name(font: Font):
    assert font.ps_name


def test_font_bold(font: Font):
    assert font.bold


def test_font_italic(font: Font):
    assert font.italic


def test_font_bold_itelic(font: Font):
    assert font.bold_italic
