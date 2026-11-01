Emblem of Gundam - English fan translation v{version}
=====================================================

Unofficial English translation patch for Emblem of Gundam (Nintendo DS, Bandai Namco Games, 2007).
No ROM is included and none will be shared. You need your own dump of the Japanese game.

Translation status
------------------
Story, briefings, battle dialogue, tutorial   Translated
Menus, units, characters, skills, messages    Translated
Stage title cards, UI graphics with text      Translated
Staff roll                                    Translated
Title logo                                    Kept (it is the game's logo)

Base ROM (required)
-------------------
Emblem of Gundam (Japan).nds
Size:   {orig[size]} bytes
CRC32:  {orig[crc32]}
MD5:    {orig[md5]}
SHA-1:  {orig[sha1]}

Patched ROM
-----------
CRC32:  {built[crc32]}
SHA-1:  {built[sha1]}

How to patch
------------
Use xdelta3 (or the web patcher at https://www.romhacking.net/patch/ or Delta Patcher):
    xdelta3 -d -s "Emblem of Gundam (Japan).nds" {patch} "Emblem of Gundam (English).nds"
If the patcher reports a checksum error, your dump differs from the one above.

Playing
-------
Tested in DeSmuME. Start a new game from a cold boot: savestates made with the Japanese game or another
patch version can hang.

Known issues
------------
A few tutorial lines read stiffly where the engine shares one line between pages.
Report problems at https://github.com/minhnhattonthat/emblem-of-gundam-en/issues

Credits
-------
Translation and hacking: minhnhattonthat, with extensive AI assistance (Claude by Anthropic).
Fonts: Liberation Sans / Liberation Serif (SIL Open Font License).
Emblem of Gundam (c) SOTSU / SUNRISE, Bandai Namco Games. This project is not affiliated with them.
