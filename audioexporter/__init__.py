import os
import shutil
import subprocess

from configloader import ConfigLoader
from versionutils import get_game_version

HEX_HEADER = "52494646"
PROCESS = {
    "localized": {
        "audio_folder": "\\Saves\\Game\\WwiseAudio\\Localized\\{folder_language}\\Media\\",
        "path_hex": "/Game/WwiseAudio/Localized/{folder_language}/Media/"
    },
    "general": {
        "audio_folder": "\\Saves\\Game\\WwiseAudio\\Media\\",
        "path_hex": "/Game/WwiseAudio/Media/"
    }
}
PROCESS_ORDER = ["localized", "general"]

PACKAGE_ROOT = os.path.join(__file__, "..", "..")
AUDIO_CONFIG = "audio_config.json"
validators = {
    "umodel_path": ConfigLoader.validate_file,
    "vgmstream_path": ConfigLoader.validate_file,
    "aes_path": ConfigLoader.validate_file,
    "valorant_path": ConfigLoader.validate_folder,
    "extract_path": ConfigLoader.validate_not_empty,
    "output_path": ConfigLoader.validate_not_empty
}

RELATIVE_GAME_EXE = "\\ShooterGame\\Binaries\\Win64\\VALORANT-Win64-Shipping.exe"
RELATIVE_PAK_FOLDER = "\\ShooterGame\\Content\\Paks\\"

DEFAULT_LANGUAGE = "en-US"


class AudioExporter:
    def __init__(self, pak_language: str, folder_language: str, game_path: str = None):
        self.config = ConfigLoader(AUDIO_CONFIG, validators)
        self.pak_language = pak_language
        self.folder_language = folder_language
        self.valorant_exe = game_path if game_path else self.config["valorant_path"] + RELATIVE_GAME_EXE

    def __apply_language_to_path(self, path: str) -> str:
        return path.replace("{pak_language}", self.pak_language) \
            .replace("{folder_language}", self.folder_language)

    def __apply_game_version_to_path(self, path: str) -> str:
        game_version = get_game_version(self.valorant_exe)
        return path.replace("{game_version}", game_version)

    def __apply_parent_file_to_path(self, path: str, parent: str) -> str:
        return path.replace("{parent}", parent)

    def __apply_audio_id_to_path(self, path: str, audio_id: str) -> str:
        return path.replace("{audio_id}", audio_id)

    def __apply_output_path(self, path: str, parent: str, audio_id: str) -> str:
        output_path = self.__apply_language_to_path(path)
        output_path = self.__apply_game_version_to_path(output_path)
        output_path = self.__apply_parent_file_to_path(output_path, parent)
        return self.__apply_audio_id_to_path(output_path, audio_id)

    def __get_archive_path(self, archive: bool, parent: str, audio_id: str) -> str:
        if not archive:
            return ""
        config = ConfigLoader(PACKAGE_ROOT + "\\" + AUDIO_CONFIG, validators)
        return self.__apply_output_path(config["output_path"], parent, audio_id)

    def export_files(self, files, process_order=["localized"], audio_paks_path: str = None,
                     output_path: str = None, archive=False):
        if isinstance(process_order, str):
            process_order = [process_order]
        output_path = output_path if output_path else self.config["output_path"]
        for file in files:
            if file.endswith(".ubulk"):
                file = file.replace(".ubulk", "")
                self.export_ubulk(file, output_path, archive)

            elif file.endswith(".uexp"):
                file = file.replace(".uexp", "")
                self.export_uexp(file, output_path, archive)

            elif file.endswith(".uasset"):
                file = file.replace(".uasset", "")
                umodel_filename, umodel_dir = AudioExporter.__separate_path(self.config["umodel_path"])
                cwd = os.getcwd()
                os.chdir(umodel_dir)
                for process in process_order:
                    self.export_uasset(umodel_filename, umodel_dir, file, output_path, process,
                                       audio_paks_path, archive)
                os.chdir(cwd)

    def export_ubulk(self, file: str, output_path: str, archive: bool):
        output_path = self.__apply_output_path(output_path, "ubulk", os.path.basename(file))
        archive_path = self.__get_archive_path(archive, "ubulk", os.path.basename(file))
        self.__parse_ubulk(file, output_path, archive_path)

    def export_uexp(self, file: str, output_path: str, archive: bool):
        self.__cleanup_uexp(file)
        output_path = self.__apply_output_path(output_path, "uexp", os.path.basename(file))
        archive_path = self.__get_archive_path(archive, "uexp", os.path.basename(file))
        self.__parse_ubulk(file, output_path, archive_path)

    def export_uasset(self, umodel_filename, umodel_dir, file, output_path, process, audio_paks_path, archive):
        audio_folder = umodel_dir + "\\" + self.__apply_language_to_path(PROCESS[process]["audio_folder"])
        path_hex = self.__apply_language_to_path(PROCESS[process]["path_hex"]).encode("utf-8").hex()

        audio_ids = self.__find_ids(file, path_hex)
        for audio_id in audio_ids:
            self.__export_id(umodel_filename, audio_id, audio_paks_path)
            audio_file = audio_folder + "\\" + audio_id
            self.__cleanup_uexp(audio_file)
            audio_output_path = self.__apply_output_path(output_path, os.path.basename(file), audio_id)
            archive_path = self.__get_archive_path(archive, os.path.basename(file), audio_id)
            self.__parse_ubulk(audio_file, audio_output_path, archive_path)

    def __parse_ubulk(self, file, output_path, archive_path):
        shutil.copy(file + ".ubulk", file + ".wem")
        subprocess1 = subprocess.Popen(
            [self.config["vgmstream_path"], "-o", output_path, file + ".wem"],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess1.wait()
        if archive_path != "":
            shutil.copy(output_path, archive_path)

    def __cleanup_uexp(self, file):
        if os.path.isfile(file + ".ubulk"):
            return
        with open(file + ".uexp", 'rb') as audio_file:
            split_audio = audio_file.read().hex().split(HEX_HEADER)
            wem_bytes = bytearray.fromhex(HEX_HEADER + split_audio[1])
            fp = open(file + ".ubulk", 'wb')
            fp.write(wem_bytes)
            fp.close()

    def __find_ids(self, file, path_hex):
        with open(file + ".uasset", 'rb') as hub_file:
            audio_ids = hub_file.read().hex().split(path_hex)
            del audio_ids[::2]
            return [bytes.fromhex(audio_id[:-18]).decode('ascii') for audio_id in audio_ids]

    def __export_id(self, umodel_filename, audio_id, audio_paks_path):
        audio_paks_path = audio_paks_path if audio_paks_path else \
            self.config["valorant_path"] + RELATIVE_PAK_FOLDER
        subprocess1 = subprocess.Popen(
            [umodel_filename, "-path=\"" + audio_paks_path + "\"",
             "-game=valorant", "-aes=@" + self.config["aes_path"], "-save", audio_id],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess1.wait()

    @staticmethod
    def __separate_path(path):
        filename = os.path.basename(path)
        base_dir = os.path.dirname(path)
        return filename, base_dir


def __select_language():
    language = input(f"[INPUT] Select language (default is '{DEFAULT_LANGUAGE}'):\n        ")
    if language == "":
        print(f"        Empty selection, using '{DEFAULT_LANGUAGE}'")
        language = DEFAULT_LANGUAGE
    return language.replace("-", "_"), language.replace("_", "-")


def __select_files():
    files_str = input(f"[INPUT] Select files to export audio from:\n        ")
    files_list = files_str.replace(" ", "").split(",")
    files = [file for file in files_list if file.endswith((".uasset", ".uexp", ".ubulk"))]
    while files_str == "" or len(files) == 0:
        files_str = input(f"        Invalid input, select files to export audio from:\n        ")
        files_list = files_str.replace(" ", "").split(",")
        files = [file for file in files_list if file.endswith((".uasset", ".uexp", ".ubulk"))]
    return files


def __select_processes():
    process_order_str = input(f"[INPUT] Select processes to run (defaults are '{', '.join(PROCESS_ORDER)}'):\n        ")
    process_order_list = process_order_str.replace(" ", "").split(",")
    process_order = [process for process in process_order_list if process in PROCESS.keys()]
    if process_order_str == "" or len(process_order) == 0:
        process_order = PROCESS_ORDER
        print(f"        Empty selection, using '{', '.join(PROCESS_ORDER)}'")
    return process_order


def __main():
    pak_language, folder_language = __select_language()
    files = __select_files()
    process_order = __select_processes()

    audio_exporter = AudioExporter(pak_language, folder_language)
    audio_exporter.export_files(files, process_order)
    print("[INFO]  Audio exported")


if __name__ == "__main__":
    __main()
