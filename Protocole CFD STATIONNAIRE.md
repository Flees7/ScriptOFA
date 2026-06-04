# Protocole CFD Stationnaire (SimpleFoam)

[**Préparation des données:	1**](#préparation-des-données:)

[**Préparation des fichiers de la simulation:	1**](#préparation-des-fichiers-de-la-simulation:)

[Se placer dans le dossier de la simulation	1](#se-placer-dans-le-dossier-de-la-simulation)

[**Préparation des dictionnaires de fonctions :	2**](#préparation-des-dictionnaires-de-fonctions-:)

[Donner les Coords et maillage standard de l'Air \- system/blockMeshDict	2](#donner-les-coords-et-maillage-standard-de-l'air---system/blockmeshdict)

[Définir les paramètres d'extraction de la maille \- system/surfaceFeatureExtractDict	3](#définir-les-paramètres-d'extraction-de-la-maille---system/surfacefeatureextractdict)

[Modifier les noms des fichiers dans system/snappyHexMeshDict	4](#modifier-les-noms-des-fichiers-dans-system/snappyhexmeshdict)

[Définir les objets avec des couches limites (ailes, pods, surfaces planes, etc)	5](#définir-les-objets-avec-des-couches-limites-\(ailes,-pods,-surfaces-planes,-etc\))

[Définir les paramètres des surfaces pour chaque composante/force dans le fichier correspondant dans le répertoire 0/	5](#définir-les-paramètres-des-surfaces-pour-chaque-composante/force-dans-le-fichier-correspondant-dans-le-répertoire-0/)

[Modifier l'aire et la hauteur de l'objet dans forceCoeffs	5](#modifier-l'aire-et-la-hauteur-de-l'objet-dans-forcecoeffs)

[**Passage à la simulation :	6**](#passage-à-la-simulation-:)

[Coller dans le shell Linux (ctrl+Maj+V) :	6](#coller-dans-le-shell-linux-\(ctrl+maj+v\)-:)

[Infos Supplémentaires :	6](#infos-supplémentaires-:)

[Supprimer les résultats de processeurs précédents en cas de plantage au début du programme	6](#supprimer-les-résultats-de-processeurs-précédents-en-cas-de-plantage-au-début-du-programme)

[Modifier les contraintes d'arrêt anticipé (résidus minimum d'arrêt, définition du niveau de détail maximum)	6](#modifier-les-contraintes-d'arrêt-anticipé-\(résidus-minimum-d'arrêt,-définition-du-niveau-de-détail-maximum\))

[Modifier la fréquence d’enregistrement des données	6](#modifier-la-fréquence-d’enregistrement-des-données)

[Relancer après un crash en changeant startTime à l'une des dernières saves	6](#relancer-après-un-crash-en-changeant-starttime-à-l'une-des-dernières-saves)

# Préparation des données: {#préparation-des-données:}

* Trouver Taille Boitier Objet  
* Déterminer position Obj/Air  
* Déterminer taille de maillage "standard" du fichier (Coefficients de division de L, l et h du bloc d'air pour obtenir des mailles cubiques)  
* Déterminer Coords refinementBox


# Préparation des fichiers de la simulation: {#préparation-des-fichiers-de-la-simulation:}

## *Se placer dans le dossier de la simulation* {#se-placer-dans-le-dossier-de-la-simulation}

#### \> cd {dossierDeTravail}

Le dossier doit contenir, avant la simulation, les dossiers “0”, “system” et “constant” (à copier des autres simulations pour le template / d'une simulation template si elle existe)

# Préparation des dictionnaires de fonctions : {#préparation-des-dictionnaires-de-fonctions-:}

## *Donner les Coords et maillage standard de l'Air \- system/blockMeshDict* {#donner-les-coords-et-maillage-standard-de-l'air---system/blockmeshdict}

#### \> nano system/blockMeshDict

## ...

## vertices

## (

##   (0 0 0\) Point 1

##   (0 1 0\)

##   ...

##   (1 1 1\) Point 8

## );

## 

## blocks

## (

##   hex (0 1 2 3 4 5 6 7\) (coeffDivL coeffDivl coeffDivh) simpleGrading (1 1 1\)

## );

## ...

## *Définir les paramètres d'extraction de la maille \- system/surfaceFeatureExtractDict* {#définir-les-paramètres-d'extraction-de-la-maille---system/surfacefeatureextractdict}

#### \> nano system/surfaceFeatureExtractDict

//Information du document générée automatiquement, ne pas modifier

## FoamFile

## {...}

## 

//Template pour définir chaque fichier d'un assemblage (objet de la simulation):

## {Nom de Fichier}.stl

## {

##   extractionMethod    extractFromSurface;

//Méthode de base de OpenFoam, a ne modifier que si on sait ce que ça fait.

## 

##   includedAngle        \[0;180\](default=150); //Angle \[0°;180°\] entre deux faces à partir duquel celles-ci seront combinées pour éviter les crevasses dans la maille (je crois).

##   

##   subsetFeatures

##   {

##       nonManifolEdges        yes|no(default); //Décide si le maillage doit inclure des arrêtes qui sont reliées à plusieurs faces

## 

##     openEdges    yes(default)|no; //Décide si le maillage doit inclure des arrêtes qui sont reliées à une unique face

##   }

##   

##   writeObj        yes(default)|no; // Décide si le maillage doit être généré en .obj pour une visualisation en post-processing plus aisée.

## } //Fin du Template, à répéter pour chaque fichier de l'assemblage.

## *Modifier les noms des fichiers dans system/snappyHexMeshDict* {#modifier-les-noms-des-fichiers-dans-system/snappyhexmeshdict}

#### \> nano system/snappyHexMeshDict

## ...

## geometry

## {

//triSurfaceMesh est le dossier dans lequel les STL sont stockés, à répéter pour chaque fichier de l'assemblage

## \[nomDuFichier\].stl {type triSurfaceMesh; name \[nom de référence que l'on veut définir pour le modèle dans ce fichier\]}

##    

## refinementBox      //zone d'air qui sera maillée à une plus haute précision/finesse.

##    {

##        type box;

##        min (coordonnées du point avec x, y et z les plus bas);

##        max (coordonnées du point avec x, y et z les plus haut);

##    } 

## }

// répétable si nécessaire pour plusieurs zone, changer le nom pour chaque nouvelle box

## castellatedMeshControl

## {

##    ...

##    features

##    (

##        {file "\[nomDuFichier\].eMesh"; level (int);} // level à laisser à 1 ou 2, il s'agit du niveau de définition de la propreté du modèle, fort impact sur la stabilité du calcul si augmenté.

       	   );  
// à répéter pour chaque fichier de l'assemblage, ne pas oublier les doubles guillemets autour du nom du fichier, le .eMesh sera généré automatiquement lors de la commande.

## 

//Définir la finesse du rafinement level haut \= rafinement fin, seules les valeurs rentrées dans hex (dans blocks) sont des niveaux acceptés

##    refinementSurfaces

##    {

##        nomDeRéférence {level (LvlMin LvlMax);} //attention au nombre d'espaces, la structure est sensible. à répéter pour chaque objet de l'assemblage

##    }  

// ne pas définir le niveau de la refinementBox ici, c'est juste en dessous que ca se définit.

## 

##    ...

##    

##    refinementRegions

##    {

##        refinementBox

##        {

##           mode inside;

          // inside implique que le niveau de raffinement va etre appliqué DANS la boite définie, il existe d'autres arguments que inside, mais ils peuvent rallonger le calcul si ils prennent une trop grosse zone

##            levels ((10 4));

##      }            //niveau de raffinement TRÈS élevé, pour simulation de turbulences par exemple, ATTENTION, si la turbulence s'échappe de cette zone de raffinement, elle peut être perdue (s'arrêter) car l'extérieur de cette zone ne pourrait pas représenter le même niveau de détail de calcul.

    //Reproductible avec chaque refinementBox définie dans geometry, ne pas oublier de leur donner des noms différents

##    }

##    

##    locationInMesh (x y z) //Remplacer x y z par les coordonnées d'un POINT qui fait parti de l'air et non pas de la pièce, permet au logiciel de déterminer quelle zone est HORS de l'assemblage et est à calculer.

##    ...

## }

## 

## ...

## *Définir les objets avec des couches limites (ailes, pods, surfaces planes, etc)* {#définir-les-objets-avec-des-couches-limites-(ailes,-pods,-surfaces-planes,-etc)}

## addLayersControls

## {

##    ...

##    layers

##    {

##        "(nom1|nom2|...|nomX).\*" //Rentrer tous les noms définis dans geometry, correspondant à des objets avec couche limite, ne pas oublier les guillemets, ne pas mettre d'espace, ne pas oublier ".\*" à la fin

##        {

##            nSurfaceLayers (int); //nombre de couche de maillage autour des objets, pour former la couche limite par itération

##        }

##        //Peut être répété avec différents ensembles d'objets de l'assemblage, pour différentes précisions sur leurs couches limites.

##    }

##    

##    … 

## }

## ...

## *Définir les paramètres des surfaces pour chaque composante/force dans le fichier correspondant dans le répertoire 0/* {#définir-les-paramètres-des-surfaces-pour-chaque-composante/force-dans-le-fichier-correspondant-dans-le-répertoire-0/}

#### nano 0/U

#### nano 0/k

#### nano 0/p

#### nano 0/omega

#### nano 0/nut

exemple : 0/U correspond à la vitesse d'écoulement fluide :

## *Modifier l'aire et la hauteur de l'objet dans forceCoeffs* {#modifier-l'aire-et-la-hauteur-de-l'objet-dans-forcecoeffs}

#### nano system/forceCoeffs

## lRef (int);

## aRef (int);

\+ indiquer les forces souhaitées

# Passage à la simulation : {#passage-à-la-simulation-:}

## *Coller dans le shell Linux (ctrl+Maj+V) :* {#coller-dans-le-shell-linux-(ctrl+maj+v)-:}

## foamCleanPolyMesh && blockMesh \> logBMesh.foam && surfaceFeatureExtract \> logSFE.foam && decomposePar \> logDeco1.foam && mpirun \-np 6 snappyHexMesh \-parallel \-overwrite | tee logSnappy.foam && reconstructParMesh \-constant \> logReco1.foam && checkMesh \> logCheckMesh.foam && decomposePar \-force \> logDeco2.foam && mpirun \-np 6 simpleFoam \-parallel | tee logSFoam.foam && reconstructPar \> logReco2.foam

On peut éventuellement rajouter \-latest à la dernière commande pour un résultat plus rapide et si on ne veut garder que la dernière itération pour les résultats.

## *Infos Supplémentaires :* {#infos-supplémentaires-:}

### Supprimer les résultats de processeurs précédents en cas de plantage au début du programme {#supprimer-les-résultats-de-processeurs-précédents-en-cas-de-plantage-au-début-du-programme}

#### rm \-rf processor\*

#### foamCleanPolyMesh

La deuxième commande permet de se débarrasser des maillages qui on planté.

### Modifier les contraintes d'arrêt anticipé (résidus minimum d'arrêt, définition du niveau de détail maximum) {#modifier-les-contraintes-d'arrêt-anticipé-(résidus-minimum-d'arrêt,-définition-du-niveau-de-détail-maximum)}

#### nano system/fvSolution

## 	SIMPLE

## {

## 	    nNonOrthogonalCorrectors 0;

## 	    consistent yes;

## 

## 	    residual control

## 	    {

## 	    	p		1e-(int); (int \-\> généralement 5 ou plus)

## 	    	U		1e-(int)  (int \-\> généralement 6 ou plus)

## 	    	“(k|omega)”	1e-(int); (int \-\> généralement 6 ou plus)

## 	    }

## 	  }

Les “relaxation factor” juste en dessous permettent de diminuer le 𝚫 des équations auxquelles ils sont associés, plus le facteur est bas, plus le calcul sera lent à converger et risque de stagner, plus le facteur est haut, plus le calcul risque de diverger. (0.5 pour p et 0.7 pour les autres en tant que standard).

### Modifier la fréquence d’enregistrement des données {#modifier-la-fréquence-d’enregistrement-des-données}

#### nano system/controlDict

## timeWrite (int); (int \-\> nb d’itérations entre chaque enregistrement de données)

### Relancer après un crash en changeant startTime à l'une des dernières saves {#relancer-après-un-crash-en-changeant-starttime-à-l'une-des-dernières-saves}

#### nano system/controlDict

## 	startTime (int); (int \-\> itération de début, doit faire partie des dossiers pré-enregistrés)