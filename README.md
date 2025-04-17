# Handleiding systeem
Voor het gebruiken van dit project, maak een -venv aan en installeer de requirements met ```pip install -r requirements.txt```
Dit installeert alle benodigde pacakges die gebruikt worden. 


Het systeem is in drie delen opgedeeld, namelijk
- Annotation
- LiveProcessing
- MachineLearningTraining

## Annotation
Annotation is voor het Annoteren van volledige Video's. Hierin zijn de volgende folders te vinden.
- annotated_images: Een folder waar de images terechtkomen, na het annoteren
- annotations: Een folder met de .txt annotaties van de images
- images: De images die geannoteerd worden, deze kunnen gegenereerd worden met ```getFramesFromVideo.py```

Het belangrijkste bestand hier is ```mainUI.py```, dit beheert de user interface en maakt met behulp van ```AutomaticAnnotation.py```
de annotaties. Dit bestand heeft een ```config.yaml``` nodig waarin alle folders staan gedefinieerd etc.

Met deze bestanden is het mogelijk om een volledig geannoteerde dataset te genereren die gebruikt kan worden voor machine learning.

## MachineLearningTraining
Bevat de .ipynb bestanden en de dataset om een machine learning model mee te trainen. !! Deze trainingen zijn op Google Colab ingericht,
zet het om zodat het importeren van de dataset werkt met een local runtime.

## LiveProcessing
De belangrijkste folder in het project, dit bevat de applicatie dat voor de gebruiker de percelen weergeeft en de data van
de detecties opslaat. Het bestaat uit de volgende folder:
- Database: Bevat het database-bestand, en ```database_handler.py``` wat de communicatie met de database beheert.
- FrameExtractor: Bevat het bestand dat frames uit een video haalt, exact hetzelfde als ```getFramesFromVideo.py``` in de annotatiefolder.
- GpsConversion: Zet de detectiepunten van het machine learning model om in Gps-coördinaat voorop een kaart. Hierbij
moeten een begin- en eind-gps-coördinaat meegegeven worden.
- ImageStitching: Bevat ```StitchRow.py``` wat gebruikt wordt bij het genereren van runs. Gebruikt vijf frames en 'stitched' deze naar 1 grotere frame,
waar het machine learning model detecties op kan uitvoeren.
- MachineLearning: Bevat de logica achter de machine learning in het project. Hierin hoort ook het .pt bestand geplaatst te worden. Dit bevat
```DetectAndPlotBatch.py``` wat detecties op meerdere frames uitvoert en de resultaten ervan in de database zet. Verder is er ook ```videoCheck.py``` om resultaten van het machinelearning model te zien.
- RunVideos: Bevat de video's die geselecteerd kunnen worden om runs mee te genereren.
- UI: Bevat de User Interface, kaart bestanden en het geoJSON bestand om de percelen in te laden. Hier zorgt ```mainUI.py``` voor de algemene aansturing van het
programma, en ```_map.html``` voor de aansturing van de kaart. 
- config.yaml: Configuratiebestand wat verschillende paths aangeeft voor het programma
- StateManager.py: Komt neer op een Main.py, dit start het programma.
                                                                    
### Zorg voor een werkende NPM installment voor de kaart
```npm init -y``` https://docs.npmjs.com/cli/v9/commands/npm-init
installeer Leaflet.js: ```npm install leaflet```


## Start programma
Om het programma te starten, zorg voor de correcte pip installaties.

```python3 StateManager.py```
