from core.structure.structure_builder import StructureBuilder


def test_structure_builder_creates_and_writes(tmp_path):
    builder = StructureBuilder(tmp_path)
    builder.clean_output()

    builder.create_directory("nested")
    builder.write_file("nested/file.txt", "content", overwrite=True)

    assert (tmp_path / "nested" / "file.txt").read_text() == "content"


def test_structure_builder_respects_overwrite(tmp_path):
    builder = StructureBuilder(tmp_path)
    target = tmp_path / "data.txt"
    target.write_text("first")

    builder.write_file("data.txt", "second", overwrite=False)

    assert target.read_text() == "first"
