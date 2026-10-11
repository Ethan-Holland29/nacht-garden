# Original games and external tools

Call of Duty: World at War and Plants vs. Zombies supply the original game content used by the private local demonstration. Their executables, maps, extracted stock scripts, art, animation data and audio are not included here. The user supplies their own installed game files.

External build/runtime dependencies include the WaW mod tools, OpenAssetTools, T4M Enhanced r48, Steam/Proton/Wine, FFmpeg, Pillow, NumPy, PyTorch, ROCm and Jupyter/IPython. Those projects retain their respective licenses and distribution terms; their binaries are not vendored here.

The original animation-attachment behavior was investigated with the public Plants vs. Zombies decompilation reference at:

- https://github.com/ruslan831/PlantsVsZombies-decompilation/blob/master/Lawn/Plant.cpp
- https://github.com/ruslan831/PlantsVsZombies-decompilation/blob/master/Sexy.TodLib/Reanimator.cpp

The repository contains integration and processing code. Stock callback fixes are applied to the user's locally extracted source during the build; full stock callback code is not checked in. Public reference implementations are not vendored.

No project-wide code license has been selected. Publishing this folder does not grant a license to the games or their assets and does not imply endorsement by their publishers or AMD.
