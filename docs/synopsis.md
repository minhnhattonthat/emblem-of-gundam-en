# Synopsis - Emblem of Gundam (NDS, 2007)

A turn-based tactics game that retells the Universal Century wars as one chronicle, "the baton of history"
(歴史のバトン). Each stage opens with a stage card of narration, then message windows with portraits (briefings,
character asides), then the battle with event dialogue; at branch points the player picks which side or front
carries the story on (e.g. ST05: space forces / ground forces; ST16: East Asia / Southeast Asia). The narrator is an
essayist-chronicler: dry, reflective, sometimes ironic, comparing "the many retellings" of these events with this one.

Eras and casts covered (official English names in glossary.md):
- **One Year War, UC 0079** (Mobile Suit Gundam): Side 7, White Base (Amuro, Bright, Sayla, Kai, Hayato, Ryu, Fraw,
  Mirai, Sleggar, Matilda, Woody), Char, Garma, Ramba Ral, the Black Tri-Stars (Gaia, Ortega, Mash), M'Quve, Dozle,
  Kycilia, Gihren, Degwin, Lalah, Challia Bull; Odessa, Jaburo, Solomon, A Baoa Qu.
- **The 08th MS Team** (ground war in Southeast Asia): Shiro Amada, Karen Joshua, Terry Sanders Jr., Michel, Eledore,
  Kiki; Aina Sahalin, Ginias Sahalin, Norris Packard.
- **War in the Pocket, 0080**: Bernard "Bernie" Wiseman, Christina Mackenzie, Al, Steiner Hardy, Mikhail Kaminsky,
  Gabriel Ramirez Garcia.
- **Stardust Memory, 0083**: Kou Uraki, South Burning, Chuck Keith, Bernard Monsha, Alpha A. Bate, Chap Adel, Nina
  Purpleton, Eiphar Synapse, Cowen, Lucette Audevie; Anavel Gato, Cima Garahau, Kelley Layzner, Karius, Aiguille
  Delaz; the Delaz Fleet and the Kanbaku (fleet review) attack, Operation Stardust.
- **Zeta Gundam, 0087**: AEUG (Kamille Bidan, Quattro Bajeena, Emma Sheen, Apolly, Roberto, Katz, Fa Yuiry, Reccoa
  Londe, Henken Bekkener, Blex Forer, Astonaige, Beltorchika Irma), Karaba, Titans (Jerid Messa, Kacricon, Lila Milla
  Rira, Mouar Pharaoh, Sarah Zabiarov, Four Murasame, Paptimus Scirocco, Yazan Gable, Rosamia Badam, Bran Blutarch,
  Jamitov Hymem, Bask Om, Jamaican Daninghan), Axis (Haman Karn, Mineva).
- Some stages are what-ifs ("Stage 06 (cut)", "Zeon Returns"); a test stage and developer rooms exist but are
  unreachable in normal play.

## Stage titles
The binding English list is `script/bbq/0000_DUMMY.json` (BBQ 0000, in stage order); `tools/lint.py` keeps each
`STnnSTAGE` string 351 identical to it and every title within the 150 px prep/brief name bar. The draft glosses
that stood here are gone: they had drifted from the shipped titles.
