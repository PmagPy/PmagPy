#!/usr/bin/env python

site_class = ['Archeologic', 'Extraterrestrial', 'Extrusive', 'Igneous', 'Intrusive', 'Lunar', 'Martian', 'Metamorphic', 'Meteorite', 'Not Specified', 'Sedimentary', 'Subaerial', 'Submarine', 'Synthetic']

site_type = ['Baked Clay', 'Baked Contact', 'Baked Mud', 'Baked Rock', 'Bath', 'Bell Mould', 'Brick', 'Burnt Floor', 'Burnt Pit', 'Burnt Structure', 'Ceramic', 'Chilled Margin', 'Concretion', 'Conglomerate', 'Delta', 'Diabase', 'Drift', 'Flow Top', 'Fresco', 'Funeral Pyre', 'Furnace', 'Furnace Slag', 'Glassy Margin', 'Hearth', 'Hypocaust', 'Impact Melt', 'Kiln', 'Laccolith', 'Lacustrine', 'Lava', 'Lava Flow', 'Metallurgical Slag', 'Mixed Archeological Objects', 'Mosaic', 'Not Specified', 'Oven', 'Pluton', 'Porcelain', 'Pot Rim', 'Pot Sherd', 'Pottery', 'Pyroclastite', 'Roof', 'Sediment Dike', 'Sediment Layer', 'Sill', 'Single Crystal', 'Slag', 'Smoking Chamber', 'Sun-Dried Object', 'Synthetic', 'Tapping Slag', 'Temple', 'Tile', 'Volcanic Ash', 'Volcanic Dike', 'Volcanic Dome', 'Volcanic Pillow', 'Volcanic Vent', 'Wall']


m = ['Mafic Dike', 'Mafic Lava', 'Mafic Tuff', 'Mafic Tuffite', 'Mafite', 'Magnesiocarbonatite', 'Magnesite-Stone', 'Magnetiteite', 'Main Pallasite', 'Main Series Eucrite', 'Mangerite', 'Marble', 'Mare Basalt Lunar Meteorite', 'Mare Gabbro Lunar Meteorite', 'Marine Clays', 'Marine Marls', 'Marls', 'Martian Achondrite', 'Meimechite', 'Melamicrogranite', 'Melilitite', 'Melilitolite', 'Melitite-rich Chondrule', 'Mesosiderite', 'Mesosiderite Silicate', 'Meta-Agglomerate', 'Meta-Andesite', 'Meta-Anorthosite', 'Meta-Arenite', 'Meta-Ash', 'Meta-Ash-Breccia', 'Meta-Basaltic-Trachyandesite', 'Meta-Olivine-Clinopyroxenite', 'Meta-Olivine-Gabbro', 'Meta-Olivine-Hornblende-Pyroxenite', 'Meta-Olivine-Melilitite', 'Meta-Olivine-Melilitolite', 'Meta-Olivine-Orthopyroxenite', 'Meta-Olivine-Pyroxene-Melilitolite', 'Meta-Olivine-Pyroxenite', 'Meta-Olivine-Websterite', 'Meta-Orthopyroxenite', 'Meta-Ultramafitite', 'Metabasalt', 'Metabasaltic-Andesite', 'Metabasanite', 'Metablock-Tephra', 'Metabomb-Tephra', 'Metabreccia', 'Metacalcite-Carbonatite', 'Metacalcite-Limestone', 'Metacalcite-Mudstone', 'Metacarbonate-Rock', 'Metacarbonatite', 'Metachert', 'Metaclinopyroxenite', 'Metaconglomerate', 'Metadacite', 'Metadiamictite', 'Metadiorite', 'Metadolerite', 'Metadolomite-Carbonatite', 'Metadolomitic Limestone', 'Metadolostone', 'Metadunite', 'Metafeldspathic-Arenite', 'Metafeldspathic-Wacke', 'Metafelsite', 'Metafoid-Syenite', 'Metafoidite', 'Metafoidolite', 'Metagabbro', 'Metagranite', 'Metagranodiorite', 'Metaharzburgite', 'Metahornblende-Pyroxenite', 'Metahyaloclastite', 'Metakimberlite', 'Metalamprophyre', 'Metalapilli-Ash', 'Metalapilli-Tephra', 'Metalapilli-Tuff', 'Metalapillistone', 'Metalatite', 'Metalime-Mudstone', 'Metalimestone', 'Metamafite', 'Metamagnesite-Stone', 'Metamelilitite', 'Metamelilitolite', 'Metamicrogranite', 'Metamonzonite', 'Metamorphic-Fault Breccia', 'Metamorphosed Tuff', 'Metamudstone', 'Metanorite', 'Metapegmatite', 'Metaperidotite', 'Metaphosphorite', 'Metapyroclastic Sediment', 'Metapyroclastic-Breccia', 'Metapyroxene-Melilitolite', 'Metapyroxene-Olivine-Melilitolite', 'Metapyroxene-Peridotite', 'Metapyroxenite', 'Metaquartz-Arenite', 'Metaquartz-Diorite', 'Metaquartz-Wacke', 'Metaquartzolite', 'Metarhyodacite', 'Metarhyolite', 'Metasandstone', 'Metashoshonite', 'Metasilicate-Claystone', 'Metasilicate-Conglomerate', 'Metasilicate-Mudstone', 'Metasilicate-Siltstone', 'Metasiliciclastic Arenaceous-Rock', 'Metasiliciclastic Argillaceous-Rock', 'Metasiliciclastic Rudaceous-Rock', 'Metasiltstone', 'Metasyenite', 'Metatephra', 'Metatephrite', 'Metatonalite', 'Metatrachyandesite', 'Metatrachybasalt', 'Metatrachydacite', 'Metatrachyte', 'Metatuffaceous-Breccia', 'Metatuffaceous-Conglomerate', 'Metatuffaceous-Gravel', 'Metatuffaceous-Mud', 'Metatuffaceous-Mudstone', 'Metatuffaceous-Sand', 'Metatuffaceous-Sandstone', 'Metatuffite', 'Metatuffsite', 'Metavolcaniclastic Siltstone', 'Metavolcaniclastic-Breccia', 'Metavolcaniclastic-Conglomerate', 'Metavolcaniclastic-Gravel', 'Metavolcaniclastic-Mud', 'Metavolcaniclastic-Mudstone', 'Metavolcaniclastic-Sand', 'Metavolcaniclastic-Sandstone', 'Metawacke', 'Metawebsterite', 'Meteorite', 'Mica Schist', 'Micaceous Mudstone', 'Micaceous Sandstone', 'Micaceous Siltstone', 'Micro-Alkali-Feldspar-Granite', 'Micro-Alkali-Feldspar-Syenite', 'Micro-Anorthosite', 'Micro-Ilmenitite', 'Micro-Orthopyroxenite', 'Microclinopyroxene-Norite', 'Microclinopyroxenite', 'Microdiorite', 'Microdunite', 'Microfoidite', 'Microfoidolite', 'Microgabbro', 'Microgabbronorite', 'Microgranite', 'Microgranodiorite', 'Microharzburgite', 'Microhornblendite', 'Microkalsilitolite', 'Microleucitolite', 'Microlherzolite', 'Micromagnetitite', 'Micromelilitolite', 'Micromonzodiorite', 'Micromonzogabbro', 'Micromonzogranite', 'Micromonzonite', 'Micromonzonorite', 'Micronephelinolite', 'Micronorite', 'Microperidotite', 'Micropyroxenite', 'Microquartzolite', 'Microsyenite', 'Microsyenogranite', 'Microtonalite', 'Microtroctolite', 'Microwebsterite', 'Microwehrlite', 'Migmatite', 'Minette', 'Monchiquite', 'Monzodiorite', 'Monzogabbro', 'Monzogranite', 'Monzonite', 'Monzonorite', 'Mud', 'Muddy Gravel', 'Muddy Sandstone', 'Muddy-Peat', 'Mudstone', 'Mugearite', 'Mylonite']
n = ['Nakhlite', 'Natrocarbonatite', 'Natron', 'Nepheline syenite', 'Nephelinite', 'Nephelinolite', 'Norite', 'Norite Lunar Meteorite', 'Not Specified', 'Novaculite', 'Nuevo Laredo Trend Eucrite']



site_lithology = {'A': ['Acapulcoite Primitive Achondrite', 'Adakite', 'Adamellite', 'Agate', 'Agglomerate', 'Alcrete', 'Alkali Basalt', 'Alkali-Feldspar-Granite', 'Alkali-Feldspar-Rhyolite', 'Alkali-Feldspar-Syenite', 'Alkali-Feldspar-Trachyte', 'Amphibolite', 'Andesite', 'Andesitic Lapilli Tuff', 'Andesitic Lava', 'Andesitic Tuff', 'Andesitic Volcaniclastic Sandstone', 'Angrite', 'Anhydrite-Stone', 'Ankerite-Boundstone', 'Ankerite-Framestone', 'Ankerite-Grainstone', 'Ankerite-Gravel', 'Ankerite-Micro-Oncolite', 'Ankerite-Microsparstone', 'Ankerite-Microstone', 'Ankerite-Mud', 'Ankerite-Mudstone', 'Ankerite-Oncolite', 'Ankerite-Oolite', 'Ankerite-Packstone', 'Ankerite-Peloidite', 'Ankerite-Pisolite', 'Ankerite-Pseudosparstone', 'Ankerite-Sand', 'Ankerite-Sparstone', 'Ankerite-Stone', 'Ankerite-Wackestone', 'Anorthosite', 'Anorthosite Lunar Meteorite', 'Anthracite', 'Aphanite', 'Aplite', 'Appinite', 'Aragonite-Boundstone', 'Aragonite-Framestone', 'Aragonite-Grainstone', 'Aragonite-Gravel', 'Aragonite-Micro-Oncolite', 'Aragonite-Microsparstone', 'Aragonite-Microstone', 'Aragonite-Mud', 'Aragonite-Mudstone', 'Aragonite-Oncolite', 'Aragonite-Oolite', 'Aragonite-Packstone', 'Aragonite-Peloidite', 'Aragonite-Pisolite', 'Aragonite-Pseudosparstone', 'Aragonite-Sand', 'Aragonite-Sparstone', 'Aragonite-Stone', 'Aragonite-Wackestone', 'Arenite', 'Ash-Breccia', 'Asteroidal Achondrite', 'Ataxite Iron Meteorite', 'Aubrite'], 'B': ['Baked Earths', 'Banded-Bright-Coal', 'Banded-Coal', 'Banded-Dull-Coal', 'Barite-Stone', 'Basalt', 'Basaltic Lava', 'Basaltic Shergottite', 'Basaltic Tuff', 'Basaltic Volcanic Breccia', 'Basaltic Volcaniclastic Sandstone', 'Basaltic trachyandesite', 'Basaltic-Andesite', 'Basaltic-Trachyandesite', 'Basanite', 'Basanitic-Foidite', 'Basin Peat', 'Bauxite', 'Bauxitic Clay', 'Benmoreite', 'Biotite-Feldspar Porphyry', 'Bituminous Mudstone', 'Bituminous-Coal', 'Black-Lignite', 'Blackband Ironstone', 'Blanket Bog Peat', 'Blastomylonite', 'Block-Tephra', 'Blue Granite', 'Blueschist', 'Bomb-Tephra', 'Bone-Coal', 'Boninite', 'Borax-Stone', 'Borolanite', 'Brachinite', 'Breccia', 'Bright-Coal', 'Brown-Lignite'], 'C': ['CB Chondrite', 'CH Chondrite', 'CI Chondrite', 'CK Chondrite', 'CM Chondrite', 'CO Chondrite', 'CR Chondrite', 'CV Chondrite', 'Ca-Al-rich Inclusion', 'Calcarenite', 'Calcareous Mudstone', 'Calcareous Pelite', 'Calcareous Psammite', 'Calcareous Sandstone', 'Calcareous Semipelite', 'Calcareous Siltstone', 'Calciocarbonatite', 'Calcite-Boundstone', 'Calcite-Carbonatite', 'Calcite-Framestone', 'Calcite-Grainstone', 'Calcite-Gravel', 'Calcite-Limestone', 'Calcite-Micro-Oncolite', 'Calcite-Microsparstone', 'Calcite-Microstone', 'Calcite-Mud', 'Calcite-Mudstone', 'Calcite-Oncolite', 'Calcite-Oolite', 'Calcite-Packstone', 'Calcite-Peloidite', 'Calcite-Pisolite', 'Calcite-Pseudosparstone', 'Calcite-Sand', 'Calcite-Sparstone', 'Calcite-Wackestone', 'Calcsilicate-Rock', 'Camptonite', 'Cannel-Coal', 'Cannel-Mudstone', 'Carbonaceous Chondrite', 'Carbonaceous Ironstone', 'Carbonaceous Mudstone', 'Carbonaceous Sandstone', 'Carbonaceous Siltstone', 'Carbonatite', 'Carnalite-Stone', 'Cataclasite', 'Cementstone', 'Chalk', 'Chalk-Rich Diamicton', 'Charnockite', 'Chassignites', 'Chert', 'Chlorite-Actinolite Metamafite', 'Chondrite', 'Chondrule', 'Chondrule Silicate', 'Chromitite', 'Clarain', 'Clay', 'Clayey Gravel', 'Clayey Sand', 'Clinopyroxene-Norite', 'Clinopyroxenite', 'Coal', 'Coal Shale', 'Coarse Silicate Sandstone', 'Colemanite-Stone', 'Comendite', 'Comenditic-Rhyolite', 'Comenditic-Trachyte', 'Conglomerate', 'Cumulate Eucrite'], 'D': ['Dacite', 'Dacitic Lapilli Tuff', 'Dacitic Lava', 'Dacitic Tuff', 'Dacitic Volcaniclastic Sandstone', 'Deep Marine Sediments', 'Diabase', 'Diamictite', 'Diamicton', 'Diatomaceous-Ooze', 'Diatomite', 'Differentiated Achondrite', 'Diogenite', 'Diorite', 'Dolerite', 'Dolomite-Boundstone', 'Dolomite-Carbonatite', 'Dolomite-Framestone', 'Dolomite-Grainstone', 'Dolomite-Gravel', 'Dolomite-Microsparstone', 'Dolomite-Microstone', 'Dolomite-Mud', 'Dolomite-Mudstone', 'Dolomite-Oncolite', 'Dolomite-Oolite', 'Dolomite-Packstone', 'Dolomite-Peloidite', 'Dolomite-Pisolite', 'Dolomite-Pseudosparstone', 'Dolomite-Sand', 'Dolomite-Sparstone', 'Dolomite-Wackestone', 'Dolomitic Limestone', 'Dolostone', 'Dull-Coal', 'Dunite', 'Durain'], 'E': ['Eclogite', 'Enderbite', 'Enstatite Chondrite', 'Epidiorite', 'Epidosite', 'Essexite', 'Eucrite', 'Extrusives'], 'F': ['Fault-Breccia', 'Feldspar Porphyry', 'Feldspathic-Arenite', 'Feldspathic-Wacke', 'Felsic Lava', 'Felsic Tuff', 'Felsic Tuffite', 'Felsite', 'Fen Peat', 'Fenite', 'Ferricrete', 'Ferroan-Carbonatite', 'Ferrocarbonatite', 'Ferruginous Limestone', 'Ferruginous Mudstone', 'Ferruginous Sandstone', 'Ferruginous Silicate Mudstone', 'Ferruginous Siltstone', 'Flint', 'Flinty Gravel', 'Foid-Bearing-Alkali-Feldspar-Microsyenite', 'Foid-Bearing-Alkali-Feldspar-Microtrachyte', 'Foid-Bearing-Alkali-Feldspar-Syenite', 'Foid-Bearing-Alkali-Feldspar-Trachyte', 'Foid-Bearing-Anorthosite', 'Foid-Bearing-Diorite', 'Foid-Bearing-Gabbro', 'Foid-Bearing-Latite', 'Foid-Bearing-Micro-Anorthosite', 'Foid-Bearing-Microdiorite', 'Foid-Bearing-Microgabbro', 'Foid-Bearing-Micromonzodiorite', 'Foid-Bearing-Micromonzogabbro', 'Foid-Bearing-Micromonzonite', 'Foid-Bearing-Microsyenite', 'Foid-Bearing-Monzodiorite', 'Foid-Bearing-Monzogabbro', 'Foid-Bearing-Monzonite', 'Foid-Bearing-Syenite', 'Foid-Bearing-Trachyte', 'Foid-Gabbro', 'Foid-Microdiorite', 'Foid-Microgabbro', 'Foid-Micromonzodiorite', 'Foid-Micromonzogabbro', 'Foid-Micromonzosyenite', 'Foid-Microsyenite', 'Foid-Monzodiorite', 'Foid-Monzogabbro', 'Foid-Monzosyenite', 'Foid-Syenite', 'Foidite', 'Foidolite', 'Forsterite Chondrite', 'Fragmental Lunar Anorthosite Breccia', 'Fusain'], 'G': ['Gabbro', 'Gabbronorite', 'Ganister', 'Gaylussite', 'Glacial Till', 'Glauconitic Sandstone', 'Gneiss', 'Gossan', 'Granite', 'Granodiorite', 'Granofels', 'Granophyre', 'Granophyric Granite', 'Granulite', 'Gravel', 'Greenschist', 'Greenstone', 'Greisen', 'Gypsum', 'Gypsum-Grainstone', 'Gypsum-Gravel', 'Gypsum-Mudstone', 'Gypsum-Packstone', 'Gypsum-Sand', 'Gypsum-Stone', 'Gypsum-Wackestone'], 'H': ['H Ordinary Chondrite', 'Halite', 'Halite-Stone', 'Harzburgite', 'Hawaiite', 'Hexahedrite Iron Meteorite', 'Hill Peat', 'Hornblende-Gabbro', 'Hornblende-Microgabbro', 'Hornblende-Microperidotite', 'Hornblende-Micropyroxenite', 'Hornblende-Peridotite', 'Hornblende-Pyroxenite', 'Hornblende-Schist', 'Hornblendite', 'Hornfels', 'Howardite', 'Hyaloclastite'], 'I': ['IAB Iron Meteorite', 'IC Iron Meteorite', 'IIAB Iron Meteorite', 'IIC Iron Meteorite', 'IID Iron Meteorite', 'IIE Iron Meteorite', 'IIE-Iron Silicate', 'IIF Iron Meteorite', 'IIG Iron Meteorite', 'IIIAB Iron Meteorite', 'IIICD Iron Meteorite', 'IIIE Iron Meteorite', 'IIIF Iron Meteorite', 'IVA Iron Meteorite', 'IVB Iron Meteorite', 'Icelandite', 'Igneous-Fault Breccia', 'Ignimbrite', 'Ijolite', 'Illite-Clay', 'Illite-Claystone', 'Ilmenitite', 'Impact-Melt Lunar Anorthosite Breccia', 'Impure-Coal', 'Intrusives', 'Iron Meteorite', 'Iron-Boundstone', 'Iron-Framestone', 'Iron-Grainstone', 'Iron-Gravel', 'Iron-Micro-Oncolite', 'Iron-Microsparstone', 'Iron-Microstone', 'Iron-Mud', 'Iron-Mudstone', 'Iron-Oncolite', 'Iron-Oolite', 'Iron-Packstone', 'Iron-Peloidite', 'Iron-Pisolite', 'Iron-Pseudosparstone', 'Iron-Sand', 'Iron-Sandstone', 'Iron-Siltstone', 'Iron-Sparstone', 'Iron-Wackestone', 'Ironstone'], 'J': ['Jadeitite', 'Jasper', 'Jasperoid'], 'K': ['Kainite-Stone', 'Kalsilitite', 'Kalsilitolite', 'Kaolinite-Clay', 'Kaolinite-Claystone', 'Kenyte', 'Kernite-Stone', 'Kersantite', 'Kieserite-Stone', 'Kimberlite', 'Komatiite'], 'L': ['L Ordinary Chondrite', 'LL Ordinary Chondrite', 'Lake Sediments', 'Lamalginite', 'Lamproite', 'Lamprophyre', 'Lapilli-Ash', 'Lapilli-Tephra', 'Lapilli-Tuff', 'Lapillistone', 'Larvikite', 'Laterite', 'Latite', 'Leucitite', 'Leucitolite', 'Leucogranite', 'Leucomicrodiorite', 'Leucomicromonzonite', 'Leucomonzogranite', 'Lherzolite', 'Lherzolitic Shergottite', 'Lignite', 'Lime-Boundstone', 'Lime-Framestone', 'Lime-Grainstone', 'Lime-Gravel', 'Lime-Micro-Oncolite', 'Lime-Microsparstone', 'Lime-Microstone', 'Lime-Mud', 'Lime-Mudstone', 'Lime-Oncolite', 'Lime-Oolite', 'Lime-Packstone', 'Lime-Peloidite', 'Lime-Pisolite', 'Lime-Pseudosparstone', 'Lime-Sand', 'Lime-Sparstone', 'Lime-Wackestone', 'Limestone', 'Limestone Gravel', 'Limey shale', 'Litchfieldite', 'Lithic-Arenite', 'Lithic-Wacke', 'Lithomarge', 'Loam', 'Lodranite Primitive Achondrite', 'Loess', 'Lunar Achondrite', 'Luxullianite'], 'M': m, 'N': n}

"""
Obsidian
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
