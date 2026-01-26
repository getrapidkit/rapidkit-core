from pathlib import Path
from typing import Union


class StructureBuilder:
    def __init__(self, output_path: Path):
        self.output_path = output_path

    def clean_output(self) -> None:
        self.output_path.mkdir(parents=True, exist_ok=True)

    def create_directory(self, relative_path: Union[str, Path]) -> None:
        dir_path = self.output_path / relative_path
        dir_path.mkdir(parents=True, exist_ok=True)

    def write_file(
        self, relative_path: Union[str, Path], content: str, overwrite: bool = True
    ) -> None:
        file_path = self.output_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not overwrite and file_path.exists():
            return

        file_path.write_text(content, encoding="utf-8")

        # If the file content looks like a script (shebang), or the path is
        # a known launcher path (.rapidkit/rapidkit), mark the file executable.
        first = content.lstrip()[:2] if content else ""

        if (
            first == "#!"
            or str(relative_path).endswith(".rapidkit/rapidkit")
            or str(relative_path).endswith("/.rapidkit/rapidkit")
        ):
            # preserve current mode and add user/group/other execute bits
            mode = file_path.stat().st_mode
            file_path.chmod(mode | 0o111)


# class StructureBuilder:
#     """
#     """

#     def __init__(self, output_path: Path):
#         self.output_path = output_path

#     def create_directory(self, relative_path: str) -> Path:
#         dir_path = self.output_path / relative_path
#         dir_path.mkdir(parents=True, exist_ok=True)
#         return dir_path

#     def write_file(
#         self, relative_path: str, content: str, overwrite: bool = False
#     ) -> Path:
#         file_path = self.output_path / relative_path
#         if file_path.exists() and not overwrite:
#             raise FileExistsError(f"File {file_path} already exists.")
#         file_path.parent.mkdir(parents=True, exist_ok=True)
#         with open(file_path, "w", encoding="utf-8") as f:
#             f.write(content)
#         return file_path

#     def copy_file(
#         self, src: Path, dest_relative_path: str, overwrite: bool = False
#     ) -> Path:
#         dest_path = self.output_path / dest_relative_path
#         if dest_path.exists() and not overwrite:
#             raise FileExistsError(f"File {dest_path} already exists.")
#         dest_path.parent.mkdir(parents=True, exist_ok=True)
#         shutil.copy2(src, dest_path)
#         return dest_path

#     def clean_output(self):
#         if self.output_path.exists():
#             shutil.rmtree(self.output_path)
#         self.output_path.mkdir(parents=True, exist_ok=True)
