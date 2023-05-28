import os
import shutil
import subprocess

from configloader import ConfigLoader
from versionutils import get_game_version

HEX_HEADER = "52494646"
AUDIO_TYPES = {
    "localized": {
        "audio_folder": "\\Saves\\Game\\WwiseAudio\\Localized\\{folder_language}\\Media\\",
        "path_hex": "/Game/WwiseAudio/Localized/{folder_language}/Media/"
    },
    "general": {
        "audio_folder": "\\Saves\\Game\\WwiseAudio\\Media\\",
        "path_hex": "/Game/WwiseAudio/Media/"
    },
    "banks": {
        "audio_folder": "\\Saves\\Game\\WwiseAudio\\Media\\{folder_language}\\"
    }
}
AUDIO_TYPE_PROCESS_ORDER = ["localized", "general"]

PACKAGE_ROOT = os.path.join(__file__, "..")
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
        client_version = get_game_version(self.valorant_exe)
        return path.replace("{game_version}", client_version["branch"] + "-" + client_version["version"])

    def __apply_parent_file_to_path(self, path: str, parent: str) -> str:
        return path.replace("{parent}", parent)

    def __apply_audio_id_to_path(self, path: str, audio_id: str) -> str:
        return path.replace("{audio_id}", audio_id)

    def __apply_output_path(self, path: str, parent: str, audio_id: str) -> str:
        output_path = self.__apply_language_to_path(path)
        output_path = self.__apply_game_version_to_path(output_path)
        output_path = self.__apply_parent_file_to_path(output_path, parent)
        return self.__apply_audio_id_to_path(output_path, audio_id)

    def __get_archive_path(self, archive: bool, parent: str, audio_id: str):
        if not archive:
            return None
        config = ConfigLoader(PACKAGE_ROOT + "\\" + AUDIO_CONFIG, validators)
        return self.__apply_output_path(config["output_path"], parent, audio_id)

    def export_audios(self, files: list, audio_types: list = ["localized"], audio_paks_path: str = None,
                      output_path: str = None, archive=False):
        if isinstance(audio_types, str):
            audio_types = [audio_types]
        audio_types = [audio_type for audio_type in audio_types if audio_type in AUDIO_TYPES.keys()]
        output_path = output_path if output_path else self.config["output_path"]
        for file in files:
            if file.endswith(".ubulk"):
                self.export_ubulk(file, output_path=output_path, archive=archive)

            elif file.endswith(".uexp"):
                self.export_uexp(file, output_path=output_path, archive=archive)

            elif file.endswith(".uasset"):
                for audio_type in audio_types:
                    self.export_uasset(file, audio_type, audio_paks_path=audio_paks_path,
                                       output_path=output_path, archive=archive)
            elif file.endswith(".bnk"):
                self.export_bank(file, audio_paks_path=audio_paks_path, output_path=output_path, archive=archive)
            else:
                for audio_type in audio_types:
                    self.export_id(file, audio_type, audio_paks_path=audio_paks_path, output_path=output_path)

    def export_ubulk(self, file: str, output_path: str = None, parent: str = None, archive: bool = False):
        parent = parent if parent else "ubulk"
        output_path = output_path if output_path else self.config["output_path"]
        file = file.replace(".ubulk", "")
        output_path = self.__apply_output_path(output_path, parent, os.path.basename(file))
        archive_path = self.__get_archive_path(archive, parent, os.path.basename(file))
        self.__parse_ubulk(file, output_path, archive_path)

    def export_uexp(self, file: str, output_path: str = None, parent: str = None, archive: bool = False):
        parent = parent if parent else "uexp"
        output_path = output_path if output_path else self.config["output_path"]
        file = file.replace(".uexp", "")
        self.__cleanup_uexp(file)
        output_path = self.__apply_output_path(output_path, parent, os.path.basename(file))
        archive_path = self.__get_archive_path(archive, parent, os.path.basename(file))
        self.__parse_ubulk(file, output_path, archive_path)

    def export_uasset(self, file: str, audio_type: str, audio_paks_path: str = None, output_path: str = None,
                      parent: str = None, archive: bool = False):
        file = file.replace(".uasset", "")
        parent = parent if parent else os.path.basename(file)
        output_path = output_path if output_path else self.config["output_path"]
        audio_folder = os.path.dirname(self.config["umodel_path"]) + "\\" + \
                       self.__apply_language_to_path(AUDIO_TYPES[audio_type]["audio_folder"])

        audio_ids = self.find_uasset_ids(file, audio_type)
        for audio_id in audio_ids:
            audio_output_path = self.__apply_output_path(output_path, parent, audio_id)
            archive_path = self.__get_archive_path(archive, parent, audio_id)
            self.__export_id(audio_id, audio_folder, audio_paks_path, audio_output_path, archive_path)

    def export_bank(self, file: str, audio_paks_path: str = None, output_path: str = None,
                    parent: str = None, archive: bool = False):
        file = file.replace(".bnk", "")
        parent = parent if parent else os.path.basename(file)
        output_path = output_path if output_path else self.config["output_path"]
        audio_folder = os.path.dirname(self.config["umodel_path"]) + "\\" + \
                       self.__apply_language_to_path(AUDIO_TYPES["banks"]["audio_folder"])

        audio_ids = AudioExporter.find_bank_ids(file)
        for audio_id in audio_ids:
            audio_output_path = self.__apply_output_path(output_path, parent, audio_id)
            archive_path = self.__get_archive_path(archive, parent, audio_id)
            self.__export_id(audio_id, audio_folder, audio_paks_path, audio_output_path, archive_path)

    def __parse_ubulk(self, file: str, output_path: str, archive_path: str):
        if not os.path.isfile(file + ".ubulk"):
            return
        shutil.copy(file + ".ubulk", file + ".wem")
        subprocess1 = subprocess.Popen(
            [self.config["vgmstream_path"], "-o", output_path, file + ".wem"],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess1.wait()
        if archive_path:
            shutil.copy(output_path, archive_path)

    def __cleanup_uexp(self, file: str):
        if os.path.isfile(file + ".ubulk"):
            return
        if not os.path.isfile(file + ".uexp"):
            return
        with open(file + ".uexp", 'rb') as audio_file:
            split_audio = audio_file.read().hex().split(HEX_HEADER)
            wem_bytes = bytearray.fromhex(HEX_HEADER + split_audio[1])
            with open(file + ".ubulk", 'wb') as ubulk_file:
                ubulk_file.write(wem_bytes)

    def find_uasset_ids(self, file: str, audio_type: str) -> list:
        path_hex = self.__apply_language_to_path(AUDIO_TYPES[audio_type]["path_hex"]).encode("utf-8").hex()
        with open(file + ".uasset", 'rb') as hub_file:
            audio_ids = hub_file.read().hex().split(path_hex)
            del audio_ids[::2]
            return [bytes.fromhex(audio_id[:-18]).decode('ascii') for audio_id in audio_ids]

    # https://wiki.xentax.com/index.php/Wwise_SoundBank_(*.bnk)#type_.232:_Sound_SFX.2FSound_Voice
    @staticmethod
    def find_bank_ids(file: str) -> list:
        with open(file + ".bnk", 'rb') as hub_file:
            bank_str = hub_file.read()
            bank_size = int.from_bytes(bank_str[4:8], byteorder="little")
            hierarchy_start = 8 + bank_size         # 4 bytes BKHD, 4 bytes for section size
            hierarchy_size = int.from_bytes(bank_str[hierarchy_start + 4:hierarchy_start + 8], byteorder="little")
            objects_start = 12 + hierarchy_start    # 4 bytes HIRC, 4 bytes for section size, 4 bytes for objects count
            sections = bank_str[objects_start:objects_start + hierarchy_size]
            working_index = 0
            audio_ids = []
            while True:
                section_type = sections[working_index]
                if section_type > 2:
                    break
                section_size = int.from_bytes(sections[working_index + 1: working_index + 5], byteorder="little")
                working_index += 5      # Already read 1 byte of type, 4 bytes of size
                if section_type == 2:
                    # Added bytes are: 4 for object ID, 4 unknown and 1 for soundbank/streamed
                    # Documentation says sounbank/streamed is 4 bytes but it's actually only 1
                    audio_id = int.from_bytes(sections[working_index + 9:working_index + 13], byteorder="little")
                    audio_ids.append(str(audio_id))
                working_index += section_size
            return audio_ids

    def export_id(self, audio_id: str, audio_type: str, audio_paks_path: str = None, output_path: str = None,
                  parent: str = None, archive: bool = False):
        parent = parent if parent else "audioID"
        output_path = output_path if output_path else self.config["output_path"]
        audio_folder = os.path.dirname(self.config["umodel_path"]) + "\\" + \
                       self.__apply_language_to_path(AUDIO_TYPES[audio_type]["audio_folder"])
        output_path = self.__apply_output_path(output_path, parent, audio_id)
        archive_path = self.__get_archive_path(archive, parent, audio_id)
        self.__export_id(audio_id, audio_folder, audio_paks_path, output_path, archive_path)

    def __export_id(self, audio_id: str, audio_folder: str, audio_paks_path: str,
                    output_path: str, archive_path: str):
        self.__extract_id(audio_id, audio_paks_path)
        audio_file = audio_folder + "\\" + audio_id
        self.__cleanup_uexp(audio_file)
        self.__parse_ubulk(audio_file, output_path, archive_path)

    def __extract_id(self, audio_id: str, audio_paks_path: str):
        audio_paks_path = audio_paks_path if audio_paks_path else \
            self.config["valorant_path"] + RELATIVE_PAK_FOLDER

        cwd = os.getcwd()
        umodel_file, umodel_dir = AudioExporter.__separate_path(self.config["umodel_path"])
        os.chdir(umodel_dir)
        subprocess1 = subprocess.Popen(
            [umodel_file, "-path=\"" + audio_paks_path + "\"",
             "-game=valorant", "-aes=@" + self.config["aes_path"], "-save", audio_id],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess1.wait()
        os.chdir(cwd)

    @staticmethod
    def __separate_path(path: str) -> tuple:
        filename = os.path.basename(path)
        base_dir = os.path.dirname(path)
        return filename, base_dir


def __select_language():
    language = input(f"[INPUT] Select language (default is '{DEFAULT_LANGUAGE}'):\n        ")
    if language == "":
        print(f"        Empty selection, using '{DEFAULT_LANGUAGE}'")
        language = DEFAULT_LANGUAGE
    return language.replace("-", "_"), language.replace("_", "-")


def __process_file_list(files_list):
    files = []
    for file in files_list:
        if os.path.isfile(file) and file.endswith((".uasset", ".ubulk", ".bnk")):
            files.append(file)
        elif os.path.isdir(file):
            sub_files = [file + "\\" + sub_file for sub_file in os.listdir(file)]
            ubulk_files = [sub_file for sub_file in sub_files if sub_file.endswith(".ubulk")]
            uasset_files = [
                sub_file for sub_file in sub_files
                if sub_file.endswith(".uasset") and sub_file.replace(".uasset", "") + ".ubulk" not in ubulk_files
            ]
            bnk_files = [sub_file for sub_file in sub_files if sub_file.endswith(".bnk")]
            files.extend(ubulk_files)
            files.extend(uasset_files)
            files.extend(bnk_files)
    return files


def __select_files():
    files_str = input(
        f"[INPUT] Select files to export audio from (audio ids, ubulk, uasset, banks or folders):\n        "
    )
    files_list = files_str.replace(" ", "").split(",")
    files = __process_file_list(files_list)
    while files_str == "" or len(files) == 0:
        files_str = input(f"        Invalid input, select files to export audio from:\n        ")
        files_list = files_str.replace(" ", "").split(",")
        files = __process_file_list(files_list)
    return files


def __select_processes():
    process_order_str = input(
        f"[INPUT] Select processes to run (defaults are '{', '.join(AUDIO_TYPE_PROCESS_ORDER)}'):\n        "
    )
    process_order_list = process_order_str.replace(" ", "").split(",")
    process_order = [process for process in process_order_list if process in AUDIO_TYPES.keys()]
    if process_order_str == "" or len(process_order) == 0:
        process_order = AUDIO_TYPE_PROCESS_ORDER
        print(f"        Empty selection, using '{', '.join(AUDIO_TYPE_PROCESS_ORDER)}'")
    return process_order


def __main():
    pak_language, folder_language = __select_language()
    files = __select_files()
    process_order = __select_processes()

    audio_exporter = AudioExporter(pak_language, folder_language)
    audio_exporter.export_audios(files, process_order)
    print("[INFO]  Audio exported")


if __name__ == "__main__":
    __main()
