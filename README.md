## AudioExporter
AudioExporter is a Python 3.8 script that extracts VALORANT's audio files into a playable WAV files. 
There are four types of exports supported by AudioExporter:
1. `.ubulk` files containing WEM content.
1. `.uexp` files when a `.ubulk` is expected but doesn't exist.
1. `.uasset` files that contain references to audio files.
1. Exporting based on audio ID.

## Package usage
#### Installation

`pip install git+https://github.com/NotToDisturb/AudioExporter.git#egg=AudioExporter`

The following tools are also required:
1. [UModel](https://www.gildor.org/en/projects/umodel)
1. [vgmstream](https://dl.vgmstream.org/)

<br>
   
#### Documentation

- [`AudioExporter`](#audioexporterpak_language-str-folder_language-str-game_path-str--none)
- [`<AudioExporter instance>.export_audios`](#audioexporter-instanceexport_audios)
- [`<AudioExporter instance>.export_ubulk`](#audioexporter-instanceexport_ubulk)
- [`<AudioExporter instance>.export_uexp`](#audioexporter-instanceexport_uexp)
- [`<AudioExporter instance>.export_ip`](#audioexporter-instanceexport_id)
- [`<AudioExporter instance>.export_uasset`](#audioexporter-instanceexport_uasset)
- [`<AudioExporter instance>.find_ids`](#audioexporter-instancefind_idsfile-str-audio_type-str---list)

<br>

> ##### `AudioExporter(pak_language: str, folder_language: str, game_path: str = None)`
> 
> Creates an instace of AudioExporter, loading the config. If `game_path` is provided, 
> it should be a path to a `VALORANT-Win64-Shipping.exe`, see more in [Example paths](#example-paths).
> 
> Check the [Config file](#config-file) section and the [ConfigLoader repo](https://github.com/NotToDisturb/ConfigLoader)
> to learn more about how the config file works.

<br>

> ##### `<AudioExporter instance>.export_audios(`
> &nbsp;&nbsp;&nbsp;&nbsp;`files: list, audio_types: list = ["localized"], audio_paks_path: str = None,`<br>
> &nbsp;&nbsp;&nbsp;&nbsp;`output_path: str = None, archive=False`<br>
> `)`
> 
> Exports and parses `files` by searching in each provided `audio_types` directory. It directs each file to its appropriate exporter
> based on the file extension.
> 
> - If provided, `audio_paks_path` will override the VALORANT path (`valorant_path` in the config)
> - If provided, `output_path` it will override the output path (`output_path` in the config)
> - If true, `archive` also copies the resulting WAV file to an archival path.
>   See more in the [Archiving](#Archiving) section.
> 
> Read more about [`audio_types`](#audio-types).

<br>

> ##### `<AudioExporter instance>.export_ubulk(`
> &nbsp;&nbsp;&nbsp;&nbsp;`file: str, output_path: str = None, parent: str = None, archive: bool = False`
> `)`
> 
> Parses a ubulk `file` by running it through vgmstream (`vgmstream_path` in the config).
> 
> - If provided, `output_path` it will override the output path (`output_path` in the config)
> - If provided, `parent` overrides the default `ubulk` parent.
> - If true, `archive` also copies the resulting WAV file to an archival path.
>   See more in the [Archiving](#Archiving) section.

<br>

> ##### `<AudioExporter instance>.export_uexp(`
> &nbsp;&nbsp;&nbsp;&nbsp;`file: str, output_path: str = None, parent: str = None, archive: bool = False`
> `)`
>
> Parses a uexp `file` by converting it to ubulk and running it through vgmstream (`vgmstream_path` in the config).
>
> - If provided, `output_path` it will override the output path (`output_path` in the config)
> - If provided, `parent` overrides the default `uexp` parent.
> - If true, `archive` also copies the resulting WAV file to an archival path.
>   See more in the [Archiving](#Archiving) section.

<br>

> ##### `<AudioExporter instance>.export_id(`
> &nbsp;&nbsp;&nbsp;&nbsp;`audio_id: str, audio_type: str, audio_paks_path: str = None,`<br>
> &nbsp;&nbsp;&nbsp;&nbsp;`output_path: str = None, parent: str = None, archive: bool = False`<br>
> `)`
> 
> Finds and exports `audio_id` from the given `audio_type` folder and parses by ensuring it is 
> ubulk and running it through vgmstream (`vgmstream_path` in the config).
>
> - If provided, `audio_paks_path` will override the VALORANT path (`valorant_path` in the config)
> - If provided, `output_path` it will override the output path (`output_path` in the config)
> - If provided, `parent` overrides the default `audioID` parent.
> - If true, `archive` also copies the resulting WAV file to an archival path.
>   See more in the [Archiving](#Archiving) section.
>
> Read more about [`audio_types`](#audio-types).

<br>

> ##### `<AudioExporter instance>.export_uasset(`
> &nbsp;&nbsp;&nbsp;&nbsp;`file: str, audio_type: str, audio_paks_path: str = None,`<br>
> &nbsp;&nbsp;&nbsp;&nbsp;`output_path: str = None, parent: str = None, archive: bool = False`<br>
> `)`
>
> Finds and exports all audio ids present in `file` from the given `audio_type` folder and 
> parses by ensuring it is ubulk and running it through vgmstream (`vgmstream_path` in the config).
>
> - If provided, `audio_paks_path` will override the VALORANT path (`valorant_path` in the config)
> - If provided, `output_path` it will override the output path (`output_path` in the config)
> - If provided, `parent` overrides the use of `file`'s filename as parent.
> - If true, `archive` also copies the resulting WAV file to an archival path.
>   See more in the [Archiving](#Archiving) section.
>
> Read more about [`audio_types`](#audio-types).

<br>

> ##### `<AudioExporter instance>.find_ids(file: str, audio_type: str) -> list`
> 
> Returns a list with all the audio ids of `audio_type` in `file`. Read more about [`audio_types`](#audio-types).

<br><br>
#### Config file
AudioExporter uses a configuration file to know where the needed tools and other paths are:

|Path             |Validation type|Description|
|-----------------|---------------|-----------|
|**umodel_path**  |File           |Path to the UModel executable.|
|**vgmstream**    |File           |Path to the vgmstream executable.|
|**aes_path**:    |File           |Path to the AES key, a text file containing only the key in `0x<key>` format.|
|**valorant_path**|Folder         |Path to your VALORANT installation folder. See more on [Example paths](#example-paths).|
|**working_path** |Folder         |Path where the extraction of audio files and its parsing to WE; will take place. |
|**output_path**  |Not empty path |Path where the parsed WAV files will be placed. Check out the available [output path keywords](#output-path-keywords).|

<br>

#### Audio types
|Type       |Description|
|-----------|-----------|
|`localized`|Audios that are present in `/Game/WwsiseAudio/Localized/{folder_language}/Media/`|
|`general`  |Audios that are present in `/Game/WwsiseAudio/Localized/Media/`

#### Example paths

|Found in|Path               |Example|
|--------|-------------------|-------|
|Code    |`game_path`        |`C:\Riot Games\VALORANT\live\ShooterGame\Binaries\Win64\VALORANT-Win64-Shipping.exe`
|Code    |`audio_paks_path`  |`C:\Riot Games\VALORANT\live\ShooterGame\Content\Paks\`
|Config  |`valorant_path`    |`C:\Riot Games\VALORANT\live\`

<br>

#### Output path keywords

|Keyword            |Description|
|-------------------|-----------|
|`{pak_language}`   |Replaced by the language of the audio file in `xx_YY` format.|
|`{folder_language}`|Replaced by the language of the audio file in `xx-YY` format.|
|`{game_version}`   |Replaced by the game version on the provided executable.|
|`{audio_id}`       |Replaced by the string of numbers identifying the audio in the game files.|
|`{parent}`         |Replaced by one of four when a `parent` argument is not provided: <ol><li>`ubulk` for `.ubulk` exports.</li><li>`uexp` for `.uexp` exports.</li><li>`audioID` for exports using the audio id.</li><li>The name of the file that refers to the audio for `.uasset` exports.</li></ol>|

<br>

#### Example usage
Here is an example of how to use AudioExporter:
```
from audioexporter import AudioExporter

NATURES_WRATH = "C:\\ProgramFiles\\UModel\\Saves\\Game\\WwiseAudio\\Localized\\en-US\\Media\\324031775.ubulk"

exporter = AudioExporter("en_US", "en-US")
exporter.export_files([NATURES_WRATH])
```
The first time this script is run, it will exit after generating `audio_config.json`.
Subsequent runs will continue exiting until the [configuration file](#config-file) is filled out correctly.
Once it is, the script will execute properly and the exported audio files will be in the output path (`output_path` in the config). 

#### Archiving
AudioExporter features an archival feature that allows the user to automatically archive 
every audio file exported. The first time a script that uses AudioExporter
is run with `archive=True`, a new config file will be generated within the installation path 
of AudioExporter (shown by the script upon generation).

That configuration can be identical to the one in your project folder, but in order to not overwrite audio files
from other versions, it is recommended that the filename of the path in `output_path` be `{parent} - {audio_id} - {folder_language}-{game_version}.wav`

## Standalone usage
It is also possible to use AudioExporter as a standalone script:

1. Download the [latest release](https://github.com/NotToDisturb/AudioExporter/releases/latest)
1. Extract the zip file
1. Open a console inside the extracted folder
1. Install the required packages using `pip install -r requirements.txt`
1. Run the script using `python audioexporter.py`

In the first execution, the config file is created and needs to be filled out.
Check out [Installation](#installation) for the tools required and 
[Config file](#config-file) for more details on how to fill out the config.<br>
Running the script after filling out the config, you will be asked for a list of files. 
Once inputted, the audio files will be exported.