#!/usr/bin/env python

site_class = ['Archeologic', 'Extraterrestrial', 'Extrusive', 'Igneous', 'Intrusive', 'Lunar', 'Martian', 'Metamorphic', 'Meteorite', 'Not Specified', 'Sedimentary', 'Subaerial', 'Submarine', 'Synthetic']

site_type = ['Baked Clay', 'Baked Contact', 'Baked Mud', 'Baked Rock', 'Bath', 'Bell Mould', 'Brick', 'Burnt Floor', 'Burnt Pit', 'Burnt Structure', 'Ceramic', 'Chilled Margin', 'Concretion', 'Conglomerate', 'Delta', 'Diabase', 'Drift', 'Flow Top', 'Fresco', 'Funeral Pyre', 'Furnace', 'Furnace Slag', 'Glassy Margin', 'Hearth', 'Hypocaust', 'Impact Melt', 'Kiln', 'Laccolith', 'Lacustrine', 'Lava', 'Lava Flow', 'Metallurgical Slag', 'Mixed Archeological Objects', 'Mosaic', 'Not Specified', 'Oven', 'Pluton', 'Porcelain', 'Pot Rim', 'Pot Sherd', 'Pottery', 'Pyroclastite', 'Roof', 'Sediment Dike', 'Sediment Layer', 'Sill', 'Single Crystal', 'Slag', 'Smoking Chamber', 'Sun-Dried Object', 'Synthetic', 'Tapping Slag', 'Temple', 'Tile', 'Volcanic Ash', 'Volcanic Dike', 'Volcanic Dome', 'Volcanic Pillow', 'Volcanic Vent', 'Wall']

site_lithology = ["too many values for now"]

site_lithology = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

site_lithology = {'A': ['one', 'two', 'three'], 'B': ['a', 'b', 'c'], 'C': ['I', 'II', 'III']}


site_lithology = {'A': ['Acapulcoite Primitive Achondrite', 'Adakite', 'Adamellite', 'Agate', 'Agglomerate', 'Alcrete', 'Alkali Basalt', 'Alkali-Feldspar-Granite', 'Alkali-Feldspar-Rhyolite', 'Alkali-Feldspar-Syenite', 'Alkali-Feldspar-Trachyte', 'Amphibolite', 'Andesite', 'Andesitic Lapilli Tuff', 'Andesitic Lava', 'Andesitic Tuff', 'Andesitic Volcaniclastic Sandstone', 'Angrite', 'Anhydrite-Stone', 'Ankerite-Boundstone', 'Ankerite-Framestone', 'Ankerite-Grainstone', 'Ankerite-Gravel', 'Ankerite-Micro-Oncolite', 'Ankerite-Microsparstone', 'Ankerite-Microstone', 'Ankerite-Mud', 'Ankerite-Mudstone', 'Ankerite-Oncolite', 'Ankerite-Oolite', 'Ankerite-Packstone', 'Ankerite-Peloidite', 'Ankerite-Pisolite', 'Ankerite-Pseudosparstone', 'Ankerite-Sand', 'Ankerite-Sparstone', 'Ankerite-Stone', 'Ankerite-Wackestone', 'Anorthosite', 'Anorthosite Lunar Meteorite', 'Anthracite', 'Aphanite', 'Aplite', 'Appinite', 'Aragonite-Boundstone', 'Aragonite-Framestone', 'Aragonite-Grainstone', 'Aragonite-Gravel', 'Aragonite-Micro-Oncolite', 'Aragonite-Microsparstone', 'Aragonite-Microstone', 'Aragonite-Mud', 'Aragonite-Mudstone', 'Aragonite-Oncolite', 'Aragonite-Oolite', 'Aragonite-Packstone', 'Aragonite-Peloidite', 'Aragonite-Pisolite', 'Aragonite-Pseudosparstone', 'Aragonite-Sand', 'Aragonite-Sparstone', 'Aragonite-Stone', 'Aragonite-Wackestone', 'Arenite', 'Ash-Breccia', 'Asteroidal Achondrite', 'Ataxite Iron Meteorite', 'Aubrite'], 'B': ['Baked Earths', 'Banded-Bright-Coal', 'Banded-Coal', 'Banded-Dull-Coal', 'Barite-Stone', 'Basalt', 'Basaltic Lava', 'Basaltic Shergottite', 'Basaltic Tuff', 'Basaltic Volcanic Breccia', 'Basaltic Volcaniclastic Sandstone', 'Basaltic trachyandesite', 'Basaltic-Andesite', 'Basaltic-Trachyandesite', 'Basanite', 'Basanitic-Foidite', 'Basin Peat', 'Bauxite', 'Bauxitic Clay', 'Benmoreite', 'Biotite-Feldspar Porphyry', 'Bituminous Mudstone', 'Bituminous-Coal', 'Black-Lignite', 'Blackband Ironstone', 'Blanket Bog Peat', 'Blastomylonite', 'Block-Tephra', 'Blue Granite', 'Blueschist', 'Bomb-Tephra', 'Bone-Coal', 'Boninite', 'Borax-Stone', 'Borolanite', 'Brachinite', 'Breccia', 'Bright-Coal', 'Brown-Lignite'], 'C': ['CB Chondrite', 'CH Chondrite', 'CI Chondrite', 'CK Chondrite', 'CM Chondrite', 'CO Chondrite', 'CR Chondrite', 'CV Chondrite', 'Ca-Al-rich Inclusion', 'Calcarenite', 'Calcareous Mudstone', 'Calcareous Pelite', 'Calcareous Psammite', 'Calcareous Sandstone', 'Calcareous Semipelite', 'Calcareous Siltstone', 'Calciocarbonatite', 'Calcite-Boundstone', 'Calcite-Carbonatite', 'Calcite-Framestone', 'Calcite-Grainstone', 'Calcite-Gravel', 'Calcite-Limestone', 'Calcite-Micro-Oncolite', 'Calcite-Microsparstone', 'Calcite-Microstone', 'Calcite-Mud', 'Calcite-Mudstone', 'Calcite-Oncolite', 'Calcite-Oolite', 'Calcite-Packstone', 'Calcite-Peloidite', 'Calcite-Pisolite', 'Calcite-Pseudosparstone', 'Calcite-Sand', 'Calcite-Sparstone', 'Calcite-Wackestone', 'Calcsilicate-Rock', 'Camptonite', 'Cannel-Coal', 'Cannel-Mudstone', 'Carbonaceous Chondrite', 'Carbonaceous Ironstone', 'Carbonaceous Mudstone', 'Carbonaceous Sandstone', 'Carbonaceous Siltstone', 'Carbonatite', 'Carnalite-Stone', 'Cataclasite', 'Cementstone', 'Chalk', 'Chalk-Rich Diamicton', 'Charnockite', 'Chassignites', 'Chert', 'Chlorite-Actinolite Metamafite', 'Chondrite', 'Chondrule', 'Chondrule Silicate', 'Chromitite', 'Clarain', 'Clay', 'Clayey Gravel', 'Clayey Sand', 'Clinopyroxene-Norite', 'Clinopyroxenite', 'Coal', 'Coal Shale', 'Coarse Silicate Sandstone', 'Colemanite-Stone', 'Comendite', 'Comenditic-Rhyolite', 'Comenditic-Trachyte', 'Conglomerate', 'Cumulate Eucrite'], 'D': ['Dacite', 'Dacitic Lapilli Tuff', 'Dacitic Lava', 'Dacitic Tuff', 'Dacitic Volcaniclastic Sandstone']}
"""
LithologiesDeep Marine Sediments
LithologiesDiabase
LithologiesDiamictite
LithologiesDiamicton
LithologiesDiatomaceous-Ooze
LithologiesDiatomite
LithologiesDifferentiated Achondrite
LithologiesDiogenite
LithologiesDiorite
LithologiesDolerite
LithologiesDolomite-Boundstone
LithologiesDolomite-Carbonatite
LithologiesDolomite-Framestone
LithologiesDolomite-Grainstone
LithologiesDolomite-Gravel
LithologiesDolomite-Microsparstone
LithologiesDolomite-Microstone
LithologiesDolomite-Mud
LithologiesDolomite-Mudstone
LithologiesDolomite-Oncolite
LithologiesDolomite-Oolite
LithologiesDolomite-Packstone
LithologiesDolomite-Peloidite
LithologiesDolomite-Pisolite
LithologiesDolomite-Pseudosparstone
LithologiesDolomite-Sand
LithologiesDolomite-Sparstone
LithologiesDolomite-Wackestone
LithologiesDolomitic Limestone
LithologiesDolostone
LithologiesDull-Coal
LithologiesDunite
LithologiesDurain
LithologiesEclogite
LithologiesEnderbite
LithologiesEnstatite Chondrite
LithologiesEpidiorite
LithologiesEpidosite
LithologiesEssexite
LithologiesEucrite
LithologiesExtrusives
LithologiesFault-Breccia
LithologiesFeldspar Porphyry
LithologiesFeldspathic-Arenite
LithologiesFeldspathic-Wacke
LithologiesFelsic Lava
LithologiesFelsic Tuff
LithologiesFelsic Tuffite
LithologiesFelsite
LithologiesFen Peat
LithologiesFenite
LithologiesFerricrete
LithologiesFerroan-Carbonatite
LithologiesFerrocarbonatite
LithologiesFerruginous Limestone
LithologiesFerruginous Mudstone
LithologiesFerruginous Sandstone
LithologiesFerruginous Silicate Mudstone
LithologiesFerruginous Siltstone
LithologiesFlint
LithologiesFlinty Gravel
LithologiesFoid-Bearing-Alkali-Feldspar-Microsyenite
LithologiesFoid-Bearing-Alkali-Feldspar-Microtrachyte
LithologiesFoid-Bearing-Alkali-Feldspar-Syenite
LithologiesFoid-Bearing-Alkali-Feldspar-Trachyte
LithologiesFoid-Bearing-Anorthosite
LithologiesFoid-Bearing-Diorite
LithologiesFoid-Bearing-Gabbro
LithologiesFoid-Bearing-Latite
LithologiesFoid-Bearing-Micro-Anorthosite
LithologiesFoid-Bearing-Microdiorite
LithologiesFoid-Bearing-Microgabbro
LithologiesFoid-Bearing-Micromonzodiorite
LithologiesFoid-Bearing-Micromonzogabbro
LithologiesFoid-Bearing-Micromonzonite
LithologiesFoid-Bearing-Microsyenite
LithologiesFoid-Bearing-Monzodiorite
LithologiesFoid-Bearing-Monzogabbro
LithologiesFoid-Bearing-Monzonite
LithologiesFoid-Bearing-Syenite
LithologiesFoid-Bearing-Trachyte
LithologiesFoid-Gabbro
LithologiesFoid-Microdiorite
LithologiesFoid-Microgabbro
LithologiesFoid-Micromonzodiorite
LithologiesFoid-Micromonzogabbro
LithologiesFoid-Micromonzosyenite
LithologiesFoid-Microsyenite
LithologiesFoid-Monzodiorite
LithologiesFoid-Monzogabbro
LithologiesFoid-Monzosyenite
LithologiesFoid-Syenite
LithologiesFoidite
LithologiesFoidolite
LithologiesForsterite Chondrite
LithologiesFragmental Lunar Anorthosite Breccia
LithologiesFusain
LithologiesGabbro
LithologiesGabbronorite
LithologiesGanister
LithologiesGaylussite
LithologiesGlacial Till
LithologiesGlauconitic Sandstone
LithologiesGneiss
LithologiesGossan
LithologiesGranite
LithologiesGranodiorite
LithologiesGranofels
LithologiesGranophyre
LithologiesGranophyric Granite
LithologiesGranulite
LithologiesGravel
LithologiesGreenschist
LithologiesGreenstone
LithologiesGreisen
LithologiesGypsum
LithologiesGypsum-Grainstone
LithologiesGypsum-Gravel
LithologiesGypsum-Mudstone
LithologiesGypsum-Packstone
LithologiesGypsum-Sand
LithologiesGypsum-Stone
LithologiesGypsum-Wackestone
LithologiesH Ordinary Chondrite
LithologiesHalite
LithologiesHalite-Stone
LithologiesHarzburgite
LithologiesHawaiite
LithologiesHexahedrite Iron Meteorite
LithologiesHill Peat
LithologiesHornblende-Gabbro
LithologiesHornblende-Microgabbro
LithologiesHornblende-Microperidotite
LithologiesHornblende-Micropyroxenite
LithologiesHornblende-Peridotite
LithologiesHornblende-Pyroxenite
LithologiesHornblende-Schist
LithologiesHornblendite
LithologiesHornfels
LithologiesHowardite
LithologiesHyaloclastite
LithologiesIAB Iron Meteorite
LithologiesIC Iron Meteorite
LithologiesIIAB Iron Meteorite
LithologiesIIC Iron Meteorite
LithologiesIID Iron Meteorite
LithologiesIIE Iron Meteorite
LithologiesIIE-Iron Silicate
LithologiesIIF Iron Meteorite
LithologiesIIG Iron Meteorite
LithologiesIIIAB Iron Meteorite
LithologiesIIICD Iron Meteorite
LithologiesIIIE Iron Meteorite
LithologiesIIIF Iron Meteorite
LithologiesIVA Iron Meteorite
LithologiesIVB Iron Meteorite
LithologiesIcelandite
LithologiesIgneous-Fault Breccia
LithologiesIgnimbrite
LithologiesIjolite
LithologiesIllite-Clay
LithologiesIllite-Claystone
LithologiesIlmenitite
LithologiesImpact-Melt Lunar Anorthosite Breccia
LithologiesImpure-Coal
LithologiesIntrusives
LithologiesIron Meteorite
LithologiesIron-Boundstone
LithologiesIron-Framestone
LithologiesIron-Grainstone
LithologiesIron-Gravel
LithologiesIron-Micro-Oncolite
LithologiesIron-Microsparstone
LithologiesIron-Microstone
LithologiesIron-Mud
LithologiesIron-Mudstone
LithologiesIron-Oncolite
LithologiesIron-Oolite
LithologiesIron-Packstone
LithologiesIron-Peloidite
LithologiesIron-Pisolite
LithologiesIron-Pseudosparstone
LithologiesIron-Sand
LithologiesIron-Sandstone
LithologiesIron-Siltstone
LithologiesIron-Sparstone
LithologiesIron-Wackestone
LithologiesIronstone
LithologiesJadeitite
LithologiesJasper
LithologiesJasperoid
LithologiesKainite-Stone
LithologiesKalsilitite
LithologiesKalsilitolite
LithologiesKaolinite-Clay
LithologiesKaolinite-Claystone
LithologiesKenyte
LithologiesKernite-Stone
LithologiesKersantite
LithologiesKieserite-Stone
LithologiesKimberlite
LithologiesKomatiite
LithologiesL Ordinary Chondrite
LithologiesLL Ordinary Chondrite
LithologiesLake Sediments
LithologiesLamalginite
LithologiesLamproite
LithologiesLamprophyre
LithologiesLapilli-Ash
LithologiesLapilli-Tephra
LithologiesLapilli-Tuff
LithologiesLapillistone
LithologiesLarvikite
LithologiesLaterite
LithologiesLatite
LithologiesLeucitite
LithologiesLeucitolite
LithologiesLeucogranite
LithologiesLeucomicrodiorite
LithologiesLeucomicromonzonite
LithologiesLeucomonzogranite
LithologiesLherzolite
LithologiesLherzolitic Shergottite
LithologiesLignite
LithologiesLime-Boundstone
LithologiesLime-Framestone
LithologiesLime-Grainstone
LithologiesLime-Gravel
LithologiesLime-Micro-Oncolite
LithologiesLime-Microsparstone
LithologiesLime-Microstone
LithologiesLime-Mud
LithologiesLime-Mudstone
LithologiesLime-Oncolite
LithologiesLime-Oolite
LithologiesLime-Packstone
LithologiesLime-Peloidite
LithologiesLime-Pisolite
LithologiesLime-Pseudosparstone
LithologiesLime-Sand
LithologiesLime-Sparstone
LithologiesLime-Wackestone
LithologiesLimestone
LithologiesLimestone Gravel
LithologiesLimey shale
LithologiesLitchfieldite
LithologiesLithic-Arenite
LithologiesLithic-Wacke
LithologiesLithomarge
LithologiesLoam
LithologiesLodranite Primitive Achondrite
LithologiesLoess
LithologiesLunar Achondrite
LithologiesLuxullianite
LithologiesMafic Dike
LithologiesMafic Lava
LithologiesMafic Tuff
LithologiesMafic Tuffite
LithologiesMafite
LithologiesMagnesiocarbonatite
LithologiesMagnesite-Stone
LithologiesMagnetiteite
LithologiesMain Pallasite
LithologiesMain Series Eucrite
LithologiesMangerite
LithologiesMarble
LithologiesMare Basalt Lunar Meteorite
LithologiesMare Gabbro Lunar Meteorite
LithologiesMarine Clays
LithologiesMarine Marls
LithologiesMarls
LithologiesMartian Achondrite
LithologiesMeimechite
LithologiesMelamicrogranite
LithologiesMelilitite
LithologiesMelilitolite
LithologiesMelitite-rich Chondrule
LithologiesMesosiderite
LithologiesMesosiderite Silicate
LithologiesMeta-Agglomerate
LithologiesMeta-Andesite
LithologiesMeta-Anorthosite
LithologiesMeta-Arenite
LithologiesMeta-Ash
LithologiesMeta-Ash-Breccia
LithologiesMeta-Basaltic-Trachyandesite
LithologiesMeta-Olivine-Clinopyroxenite
LithologiesMeta-Olivine-Gabbro
LithologiesMeta-Olivine-Hornblende-Pyroxenite
LithologiesMeta-Olivine-Melilitite
LithologiesMeta-Olivine-Melilitolite
LithologiesMeta-Olivine-Orthopyroxenite
LithologiesMeta-Olivine-Pyroxene-Melilitolite
LithologiesMeta-Olivine-Pyroxenite
LithologiesMeta-Olivine-Websterite
LithologiesMeta-Orthopyroxenite
LithologiesMeta-Ultramafitite
LithologiesMetabasalt
LithologiesMetabasaltic-Andesite
LithologiesMetabasanite
LithologiesMetablock-Tephra
LithologiesMetabomb-Tephra
LithologiesMetabreccia
LithologiesMetacalcite-Carbonatite
LithologiesMetacalcite-Limestone
LithologiesMetacalcite-Mudstone
LithologiesMetacarbonate-Rock
LithologiesMetacarbonatite
LithologiesMetachert
LithologiesMetaclinopyroxenite
LithologiesMetaconglomerate
LithologiesMetadacite
LithologiesMetadiamictite
LithologiesMetadiorite
LithologiesMetadolerite
LithologiesMetadolomite-Carbonatite
LithologiesMetadolomitic Limestone
LithologiesMetadolostone
LithologiesMetadunite
LithologiesMetafeldspathic-Arenite
LithologiesMetafeldspathic-Wacke
LithologiesMetafelsite
LithologiesMetafoid-Syenite
LithologiesMetafoidite
LithologiesMetafoidolite
LithologiesMetagabbro
LithologiesMetagranite
LithologiesMetagranodiorite
LithologiesMetaharzburgite
LithologiesMetahornblende-Pyroxenite
LithologiesMetahyaloclastite
LithologiesMetakimberlite
LithologiesMetalamprophyre
LithologiesMetalapilli-Ash
LithologiesMetalapilli-Tephra
LithologiesMetalapilli-Tuff
LithologiesMetalapillistone
LithologiesMetalatite
LithologiesMetalime-Mudstone
LithologiesMetalimestone
LithologiesMetamafite
LithologiesMetamagnesite-Stone
LithologiesMetamelilitite
LithologiesMetamelilitolite
LithologiesMetamicrogranite
LithologiesMetamonzonite
LithologiesMetamorphic-Fault Breccia
LithologiesMetamorphosed Tuff
LithologiesMetamudstone
LithologiesMetanorite
LithologiesMetapegmatite
LithologiesMetaperidotite
LithologiesMetaphosphorite
LithologiesMetapyroclastic Sediment
LithologiesMetapyroclastic-Breccia
LithologiesMetapyroxene-Melilitolite
LithologiesMetapyroxene-Olivine-Melilitolite
LithologiesMetapyroxene-Peridotite
LithologiesMetapyroxenite
LithologiesMetaquartz-Arenite
LithologiesMetaquartz-Diorite
LithologiesMetaquartz-Wacke
LithologiesMetaquartzolite
LithologiesMetarhyodacite
LithologiesMetarhyolite
LithologiesMetasandstone
LithologiesMetashoshonite
LithologiesMetasilicate-Claystone
LithologiesMetasilicate-Conglomerate
LithologiesMetasilicate-Mudstone
LithologiesMetasilicate-Siltstone
LithologiesMetasiliciclastic Arenaceous-Rock
LithologiesMetasiliciclastic Argillaceous-Rock
LithologiesMetasiliciclastic Rudaceous-Rock
LithologiesMetasiltstone
LithologiesMetasyenite
LithologiesMetatephra
LithologiesMetatephrite
LithologiesMetatonalite
LithologiesMetatrachyandesite
LithologiesMetatrachybasalt
LithologiesMetatrachydacite
LithologiesMetatrachyte
LithologiesMetatuffaceous-Breccia
LithologiesMetatuffaceous-Conglomerate
LithologiesMetatuffaceous-Gravel
LithologiesMetatuffaceous-Mud
LithologiesMetatuffaceous-Mudstone
LithologiesMetatuffaceous-Sand
LithologiesMetatuffaceous-Sandstone
LithologiesMetatuffite
LithologiesMetatuffsite
LithologiesMetavolcaniclastic Siltstone
LithologiesMetavolcaniclastic-Breccia
LithologiesMetavolcaniclastic-Conglomerate
LithologiesMetavolcaniclastic-Gravel
LithologiesMetavolcaniclastic-Mud
LithologiesMetavolcaniclastic-Mudstone
LithologiesMetavolcaniclastic-Sand
LithologiesMetavolcaniclastic-Sandstone
LithologiesMetawacke
LithologiesMetawebsterite
LithologiesMeteorite
LithologiesMica Schist
LithologiesMicaceous Mudstone
LithologiesMicaceous Sandstone
LithologiesMicaceous Siltstone
LithologiesMicro-Alkali-Feldspar-Granite
LithologiesMicro-Alkali-Feldspar-Syenite
LithologiesMicro-Anorthosite
LithologiesMicro-Ilmenitite
LithologiesMicro-Orthopyroxenite
LithologiesMicroclinopyroxene-Norite
LithologiesMicroclinopyroxenite
LithologiesMicrodiorite
LithologiesMicrodunite
LithologiesMicrofoidite
LithologiesMicrofoidolite
LithologiesMicrogabbro
LithologiesMicrogabbronorite
LithologiesMicrogranite
LithologiesMicrogranodiorite
LithologiesMicroharzburgite
LithologiesMicrohornblendite
LithologiesMicrokalsilitolite
LithologiesMicroleucitolite
LithologiesMicrolherzolite
LithologiesMicromagnetitite
LithologiesMicromelilitolite
LithologiesMicromonzodiorite
LithologiesMicromonzogabbro
LithologiesMicromonzogranite
LithologiesMicromonzonite
LithologiesMicromonzonorite
LithologiesMicronephelinolite
LithologiesMicronorite
LithologiesMicroperidotite
LithologiesMicropyroxenite
LithologiesMicroquartzolite
LithologiesMicrosyenite
LithologiesMicrosyenogranite
LithologiesMicrotonalite
LithologiesMicrotroctolite
LithologiesMicrowebsterite
LithologiesMicrowehrlite
LithologiesMigmatite
LithologiesMinette
LithologiesMonchiquite
LithologiesMonzodiorite
LithologiesMonzogabbro
LithologiesMonzogranite
LithologiesMonzonite
LithologiesMonzonorite
LithologiesMud
LithologiesMuddy Gravel
LithologiesMuddy Sandstone
LithologiesMuddy-Peat
LithologiesMudstone
LithologiesMugearite
LithologiesMylonite
LithologiesNakhlite
LithologiesNatrocarbonatite
LithologiesNatron
LithologiesNepheline syenite
LithologiesNephelinite
LithologiesNephelinolite
LithologiesNorite
LithologiesNorite Lunar Meteorite
LithologiesNot Specified
LithologiesNovaculite
LithologiesNuevo Laredo Trend Eucrite
LithologiesObsidian
LithologiesOctahedrite Iron Meteorite
LithologiesOlistostrome
LithologiesOlivine Chondrule
LithologiesOlivine Diorite
LithologiesOlivine Monzonite
LithologiesOlivine-Clinopyroxene-Micronorite
LithologiesOlivine-Clinopyroxene-Norite
LithologiesOlivine-Clinopyroxenite
LithologiesOlivine-Gabbro
LithologiesOlivine-Gabbronorite
LithologiesOlivine-Hornblende-Micropyroxenite
LithologiesOlivine-Hornblende-Pyroxenite
LithologiesOlivine-Hornblendite
LithologiesOlivine-Melilitite
LithologiesOlivine-Melilitolite
LithologiesOlivine-Micro-Orthopyroxenite
LithologiesOlivine-Microclinopyroxenite
LithologiesOlivine-Microgabbro
LithologiesOlivine-Microgabbronorite
LithologiesOlivine-Microhornblendite
LithologiesOlivine-Micromelilitolite
LithologiesOlivine-Micronorite
LithologiesOlivine-Micropyroxenite
LithologiesOlivine-Microwebsterite
LithologiesOlivine-Norite
LithologiesOlivine-Orthopyroxene-Gabbro
LithologiesOlivine-Orthopyroxene-Microgabbro
LithologiesOlivine-Orthopyroxenite
LithologiesOlivine-Pyroxene-Hornblendite
LithologiesOlivine-Pyroxene-Kalsilitolite
LithologiesOlivine-Pyroxene-Melilitolite
LithologiesOlivine-Pyroxene-Microhornblendite
LithologiesOlivine-Pyroxene-Microkalsilitolite
LithologiesOlivine-Pyroxene-Micromelilitolite
LithologiesOlivine-Pyroxenite
LithologiesOlivine-Websterite
LithologiesOolitic Limestone
LithologiesOpaline-Chert
LithologiesOpaline-Porcellanite
LithologiesOrdinary Chondrite
LithologiesOrganic Clay
LithologiesOrganic Mud
LithologiesOrganic Sand
LithologiesOrganic Silt
LithologiesOrtho-Amphibolite
LithologiesOrthogneiss
LithologiesOrthogranofels
LithologiesOrthopyroxene-Gabbro
LithologiesOrthopyroxene-Microgabbro
LithologiesOrthopyroxenite
LithologiesOrthoschist
LithologiesPallasite
LithologiesPallasite Olivine
LithologiesPantellerite
LithologiesPantelleritic-Rhyolite
LithologiesPantelleritic-Trachyte
LithologiesPara-Amphibolite
LithologiesParagneiss
LithologiesParagranofels
LithologiesParaschist
LithologiesPeat
LithologiesPebbly Clay
LithologiesPebbly Mudstone
LithologiesPebbly Sandstone
LithologiesPebbly Siltstone
LithologiesPegmatite
LithologiesPegmatitic Granite
LithologiesPelite
LithologiesPeridotite
LithologiesPhonolite
LithologiesPhonolitic-Basanite
LithologiesPhonolitic-Foidite
LithologiesPhonolitic-Tephrite
LithologiesPhosphate-Boundstone
LithologiesPhosphate-Framestone
LithologiesPhosphate-Grainstone
LithologiesPhosphate-Gravel
LithologiesPhosphate-Micro-Oncolite
LithologiesPhosphate-Microsparstone
LithologiesPhosphate-Microstone
LithologiesPhosphate-Mud
LithologiesPhosphate-Mudstone
LithologiesPhosphate-Oncolite
LithologiesPhosphate-Oolite
LithologiesPhosphate-Packstone
LithologiesPhosphate-Peloidite
LithologiesPhosphate-Pisolite
LithologiesPhosphate-Pseudosparstone
LithologiesPhosphate-Sand
LithologiesPhosphate-Sandstone
LithologiesPhosphate-Sparstone
LithologiesPhosphate-Wackestone
LithologiesPhosphatic Mudstone
LithologiesPhosphorite
LithologiesPhyllite
LithologiesPhyllonite
LithologiesPicrite
LithologiesPitchstone
LithologiesPolyhalite-Stone
LithologiesPolymict Eucrite
LithologiesPorcellanite
LithologiesPorphyritic Basalt
LithologiesPorphyry
LithologiesPotassic-Trachybasalt
LithologiesPrimitive Achondrite
LithologiesProtocataclasite
LithologiesProtomylonite
LithologiesPsammite
LithologiesPseudotachylite
LithologiesPumice
LithologiesPyroclastic-Breccia
LithologiesPyrolite
LithologiesPyroxene Pallasite
LithologiesPyroxene-Hornblende-Clinopyroxene-Micronorite
LithologiesPyroxene-Hornblende-Clinopyroxene-Norite
LithologiesPyroxene-Hornblende-Gabbro
LithologiesPyroxene-Hornblende-Gabbronorite
LithologiesPyroxene-Hornblende-Microgabbro
LithologiesPyroxene-Hornblende-Microgabbronorite
LithologiesPyroxene-Hornblende-Micronorite
LithologiesPyroxene-Hornblende-Microperidotite
LithologiesPyroxene-Hornblende-Norite
LithologiesPyroxene-Hornblende-Orthopyroxene-Gabbro
LithologiesPyroxene-Hornblende-Orthopyroxene-Microgabbro
LithologiesPyroxene-Hornblende-Peridotite
LithologiesPyroxene-Hornblendite
LithologiesPyroxene-Melilitolite
LithologiesPyroxene-Microhornblendite
LithologiesPyroxene-Micromelilitolite
LithologiesPyroxene-Microperidotite
LithologiesPyroxene-Olivine-Melilitolite
LithologiesPyroxene-Peridotite
LithologiesPyroxenite
LithologiesQuartz Feldspar Porphyry
LithologiesQuartz diorite
LithologiesQuartz monzonite
LithologiesQuartz-Alkali-Feldspar-Microsyenite
LithologiesQuartz-Alkali-Feldspar-Syenite
LithologiesQuartz-Alkali-Feldspar-Trachyte
LithologiesQuartz-Anorthosite
LithologiesQuartz-Arenite
LithologiesQuartz-Biotite Norite
LithologiesQuartz-Diorite
LithologiesQuartz-Gabbro
LithologiesQuartz-Latite
LithologiesQuartz-Micro-Anorthosite
LithologiesQuartz-Microdiorite
LithologiesQuartz-Microgabbro
LithologiesQuartz-Micromonzodiorite
LithologiesQuartz-Micromonzogabbro
LithologiesQuartz-Micromonzonite
LithologiesQuartz-Micronorite
LithologiesQuartz-Microsyenite
LithologiesQuartz-Monzodiorite
LithologiesQuartz-Monzogabbro
LithologiesQuartz-Monzonite
LithologiesQuartz-Norite
LithologiesQuartz-Syenite
LithologiesQuartz-Trachyte
LithologiesQuartz-Wacke
LithologiesQuartzite
LithologiesQuartzolite
LithologiesQuartzose-Chert
LithologiesQuartzose-Porcellanite
LithologiesRadiolarian-Ooze
LithologiesRadiolarite
LithologiesRapakivi granite
LithologiesRed Silt
LithologiesRedbeds
LithologiesRegolith Lunar Anorthosite Breccia
LithologiesRhomb porphyry
LithologiesRhyodacite
LithologiesRhyodactic Lava
LithologiesRhyodactic Tuff
LithologiesRhyolite
LithologiesRhyolitic Lapilli Tuff
LithologiesRhyolitic Lava
LithologiesRhyolitic Tuff
LithologiesRhyolitic Volcaniclastic Sandstone
LithologiesRodingites
LithologiesRumurutiite Chondrite
LithologiesSandstone
LithologiesSandy Clay
LithologiesSandy Dolostone
LithologiesSandy Limestone
LithologiesSandy Mudstone
LithologiesSandy-Clayey-Gravel
LithologiesSandy-Clayey-Sediment
LithologiesSandy-Peat
LithologiesSannaite
LithologiesSapropelic-Lignite
LithologiesSapropelite
LithologiesSchist
LithologiesScoria
LithologiesSeatearth Claystone
LithologiesSeatearth Mudstone
LithologiesSeatearth Sandstone
LithologiesSeatearth Siltstone
LithologiesSedimentary-Fault Breccia
LithologiesSelenite
LithologiesSemipelite
LithologiesSerpentinite
LithologiesShallow Marine Sediments
LithologiesShell Marl
LithologiesShell-Lime-Sediment
LithologiesShelly Ironstone
LithologiesShelly Sandstone
LithologiesShelly Siltstone
LithologiesShergottite
LithologiesShonkinite
LithologiesShoshonite
LithologiesSiderite-Mudstone
LithologiesSilicate-Clay
LithologiesSilicate-Conglomerate
LithologiesSilicate-Gravel
LithologiesSilicate-Mud
LithologiesSilicate-Mudstone
LithologiesSilicate-Sand
LithologiesSilicate-Sandstone
LithologiesSilicate-Silt
LithologiesSilicate-Siltstone
LithologiesSiliceous Organic Mudstone
LithologiesSiliceous Rocks
LithologiesSiliceous-Ooze
LithologiesSilt
LithologiesSiltstone
LithologiesSilty Clay
LithologiesSilty Mudstone
LithologiesSilty Sand
LithologiesSilty Sandstone
LithologiesSinter
LithologiesSkarn
LithologiesSlate
LithologiesSmectite-Clay
LithologiesSmectite-Claystone
LithologiesSoapstone
LithologiesSoil
LithologiesSovite
LithologiesSpessartite
LithologiesSpiculite
LithologiesSponge-Spicular-Ooze
LithologiesStannern Trend Eucrite
LithologiesStony Iron Meteorite
LithologiesStony Meteorite
LithologiesStructurally Clasified Iron Meteorite
LithologiesSubfeldspathic-Arenite
LithologiesSublithic-Arenite
LithologiesSubmarine Basaltic Glass
LithologiesSuevite
LithologiesSyenite
LithologiesSyenogranite
LithologiesSylvite-Stone
LithologiesSynthetic
LithologiesTachylyte
LithologiesTaconite
LithologiesTalc-Carbonate
LithologiesTalc-Rock
LithologiesTelaginite
LithologiesTephrite
LithologiesTephritic-Foidite
LithologiesTephritic-Phonolite
LithologiesTeschenite
LithologiesTheralite
LithologiesThermonatrite
LithologiesTholeiite
LithologiesTonalite
LithologiesTrachyandesite
LithologiesTrachybasalt
LithologiesTrachydacite
LithologiesTrachyte
LithologiesTrachytic Tuff
LithologiesTrachytic-Lava
LithologiesTransitional Shergottite
LithologiesTroctolite
LithologiesTrona
LithologiesTrondhjemite
LithologiesTuff
LithologiesTuff-Breccia
LithologiesTuffaceous-Breccia
LithologiesTuffaceous-Conglomerate
LithologiesTuffaceous-Gravel
LithologiesTuffaceous-Mud
LithologiesTuffaceous-Mudstone
LithologiesTuffaceous-Sand
LithologiesTuffaceous-Sandstone
LithologiesTuffaceous-Siltstone
LithologiesTuffisite
LithologiesTuffite
LithologiesTurbidites
LithologiesUlexite-Stone
LithologiesUltracataclasite
LithologiesUltramafitite
LithologiesUltramylonite
LithologiesUncategorized Achondrite
LithologiesUreilite Primitive Achondrite
LithologiesUrelite
LithologiesVariolite
LithologiesVesta Achondrite
LithologiesVitrain
LithologiesVogesite
LithologiesVolcaniclastic
LithologiesVolcaniclastic-Breccia
LithologiesVolcaniclastic-Conglomerate
LithologiesVolcaniclastic-Gravel
LithologiesVolcaniclastic-Mud
LithologiesVolcaniclastic-Mudstone
LithologiesVolcaniclastic-Sand
LithologiesVolcaniclastic-Sandstone
LithologiesVolcaniclastic-Siltstone
LithologiesWacke
LithologiesWebsterite
LithologiesWehrlite
LithologiesWinonaite Primitive Achondrite
"""

site_definition = ['s', 'c']


location_type = ['Archeological Site', 'Core', 'Drill Site', 'Lake Core', 'Land Section', 'Lunar', 'Martian', 'Outcrop', 'Region', 'Stratigraphic Section', 'Submarine Site']

age_units = ['Ga', 'Ka', 'Ma', 'Years AD (+/-)', 'Years BP', 'Years Cal AD (+/-)', 'Years Cal BP']

geochronology_method_codes = ['GM-ALPHA', 'GM-ARAR', 'GM-ARAR-AP', 'GM-ARAR-II', 'GM-ARAR-IS', 'GM-ARAR-NI', 'GM-ARAR-SC', 'GM-ARAR-SC-10', 'GM-ARAR-SC-1050', 'GM-ARAR-SC-50', 'GM-ARAR-TF', 'GM-C14', 'GM-C14-AMS', 'GM-C14-BETA', 'GM-C14-CAL', 'GM-CC', 'GM-CC-ARCH', 'GM-CC-ARM', 'GM-CC-ASTRO', 'GM-CC-CACO3', 'GM-CC-COLOR', 'GM-CC-GRAPE', 'GM-CC-IRM', 'GM-CC-ISO', 'GM-CC-REL', 'GM-CC-S', 'GM-CC-STRAT', 'GM-CC-TECT', 'GM-CC-TEPH', 'GM-CC-X', 'GM-CHEM', 'GM-CHEM-AAR', 'GM-CHEM-OH', 'GM-CHEM-SC', 'GM-CHEM-TH', 'GM-COSMO', 'GM-COSMO-AL26', 'GM-COSMO-AR39', 'GM-COSMO-BE10', 'GM-COSMO-C14', 'GM-COSMO-CL36', 'GM-COSMO-HE3', 'GM-COSMO-KR81', 'GM-COSMO-NE21', 'GM-COSMO-NI59', 'GM-COSMO-SI32', 'GM-DENDRO', 'GM-ESR', 'GM-FOSSIL', 'GM-FT', 'GM-HIST', 'GM-INT', 'GM-INT-L', 'GM-INT-S', 'GM-ISO', 'GM-KAR', 'GM-KAR-C', 'GM-KAR-I', 'GM-KAR-MA', 'GM-KCA', 'GM-KCA-I', 'GM-KCA-MA', 'GM-LABA', 'GM-LABA-I', 'GM-LABA-MA', 'GM-LACE', 'GM-LACE-I', 'GM-LACE-MA', 'GM-LICHE', 'GM-LUHF', 'GM-LUHF-I', 'GM-LUHF-MA', 'GM-LUM', 'GM-LUM-IRS', 'GM-LUM-OS', 'GM-LUM-TH', 'GM-MOD', 'GM-MOD-L', 'GM-MOD-S', 'GM-MORPH', 'GM-MORPH-DEF', 'GM-MORPH-DEP', 'GM-MORPH-POS', 'GM-MORPH-WEATH', 'GM-NO', 'GM-O18', 'GM-PBPB', 'GM-PBPB-C', 'GM-PBPB-I', 'GM-PLEO', 'GM-PMAG-ANOM', 'GM-PMAG-APWP', 'GM-PMAG-ARCH', 'GM-PMAG-DIR', 'GM-PMAG-POL', 'GM-PMAG-REGSV', 'GM-PMAG-RPI', 'GM-PMAG-VEC', 'GM-RATH', 'GM-RBSR', 'GM-RBSR-I', 'GM-RBSR-MA', 'GM-REOS', 'GM-REOS-I', 'GM-REOS-MA', 'GM-REOS-PT', 'GM-SCLERO', 'GM-SHRIMP', 'GM-SMND', 'GM-SMND-I', 'GM-SMND-MA', 'GM-THPB', 'GM-THPB-I', 'GM-THPB-MA', 'GM-UPA', 'GM-UPB', 'GM-UPB-CC-T0', 'GM-UPB-CC-T1', 'GM-UPB-I-206', 'GM-UPB-I-207', 'GM-UPB-MA-206', 'GM-UPB-MA-207', 'GM-USD', 'GM-USD-PA231-TH230', 'GM-USD-PA231-U235', 'GM-USD-PB210', 'GM-USD-RA226-TH230', 'GM-USD-RA228-TH232', 'GM-USD-TH228-TH232', 'GM-USD-TH230', 'GM-USD-TH230-TH232', 'GM-USD-TH230-U234', 'GM-USD-TH230-U238', 'GM-USD-U234-U238', 'GM-UTH', 'GM-UTHHE', 'GM-UTHPB', 'GM-UTHPB-CC-T0', 'GM-UTHPB-CC-T1', 'GM-VARV']
