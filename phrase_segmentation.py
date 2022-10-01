from pprint import pformat
from conllu import parse 
import os
import requests


INPUT_FILE = "file_name.txt" # the name of the file for segmentation (or the path to this file); use only the txt files and UTF-8 coding
OUTPUT_FILE = "segmented_text_file_name.txt" # name of the file for saving the results of segmentation


def bez_interpunkce(veta):
    """vyhodí z věty interpunkční znaménka bo v UD tvoří samostatné tokeny"""

    return veta.filter(xpos=lambda x: x != "Z:-------------") 


def hledani_predikatu(poradi_vety):
    """najde predikáty v dané větě a uloží jejich id a form"""

    predikaty_id = []
    predikaty_form = []
    morfo_kategorie_predikatu = ("VB", "Vp", "Vi", "Vs")
    aktualni_veta = parsovani[poradi_vety]
    aktualni_veta = bez_interpunkce(aktualni_veta)
    for token in aktualni_veta:

        if token["upos"] == "VERB" and token["xpos"][0:2] in morfo_kategorie_predikatu:
            if token["id"] not in predikaty_id:
                predikaty_id.append(token["id"])
                predikaty_form.append(token["form"])

        if token["upos"] == "AUX" and token["xpos"][0:2] in morfo_kategorie_predikatu:
            nominalni_cast_id = int(token["head"])
            for token_pomocny in aktualni_veta:
                if token_pomocny["id"] == nominalni_cast_id:
                    if token_pomocny["id"] not in predikaty_id:
                        predikaty_id.append(token_pomocny["id"])
                        predikaty_form.append(token_pomocny["form"])
        
            if nominalni_cast_id == 0:   # tuhle podmínku jsem přidala
                predikaty_id.append(token["id"])
                predikaty_form.append(token["form"])

    return predikaty_id, predikaty_form

def hledani_frazi(poradi_vety, hlava, predikaty_vety):
    """najde hlavy frází (=přímé uzly) jednotlivých klauzí; uloží, aby zachováno info o struktuře věta-klauze-fráze"""

    hlavy_frazi_klauze_id = []
    hlavy_frazi_klauze_form = []

    aktualni_veta = parsovani[poradi_vety]
    aktualni_veta = bez_interpunkce(aktualni_veta)

    for token in aktualni_veta:
        if token["id"] != hlava and token["id"] not in predikaty_vety and token["head"] == hlava:
            hlavy_frazi_klauze_id.append(token["id"])
            hlavy_frazi_klauze_form.append(token["form"])

    return hlavy_frazi_klauze_id, hlavy_frazi_klauze_form


def hledani_slov_frazi(poradi_vety, hlavy, predikaty):
    """najde všechna slova frází (rekurzivní funkce); uloží, aby zachováno info o struktuře věta-fráze-slovo"""
    aktualni_veta = parsovani[poradi_vety]
    aktualni_veta = bez_interpunkce(aktualni_veta)
    nove_hlavy = []
    

    if len(hlavy) == 0:
        return

    else:
        for token in aktualni_veta:
            if token["id"] not in predikaty and token["id"] not in hlavy and token["head"] in hlavy:
                nove_hlavy.append(token["id"])
                slova_fraze_id.append(token["id"])
                slova_fraze_form.append(token["form"])
                
    
    hledani_slov_frazi(poradi_vety, nove_hlavy, predikaty)

    return 
    

### here the fun begins

text = INPUT_FILE
soubor = open(text, encoding="UTF-8")

# UDPipe parsing
data_z_webu = requests.post('http://lindat.mff.cuni.cz/services/udpipe/api/process', data={'tokenizer': "", 'tagger': "", 'parser': ""}, files={"data": soubor})
soubor.close()
data = data_z_webu.json()['result'] 

# python lib conllu processing
parsovani = parse(data)

# solving of problematic places (UD processing of conditional)
for veta in parsovani:
    for token_pomocny in veta: 
        if type(token_pomocny["id"]) is not int: 
            id_pomocne = token_pomocny["id"][0] 
            form_pomocne = token_pomocny["form"] 
            for token_pomocny_dva in veta:
                if token_pomocny_dva["id"] == id_pomocne:
                    token_pomocny_dva["head"] = None 


# saving information about sentences
vety_infa = []
fraze_slova = []
for poradi_vety, veta in enumerate(parsovani):

    veta_info = {}
    veta_info["id věty"] = int(veta.metadata["sent_id"])
    #veta_info["text"] = veta.metadata["text"] # uložení textu věty
    veta_info["predikáty id"], veta_info["predikáty form"] = hledani_predikatu(poradi_vety)
    veta_info["délka v počtu klauzí"] = len(veta_info["predikáty id"])
    veta_info["klauze infa"] = []
    vety_infa.append(veta_info)

for poradi_vety, veta_info in enumerate(vety_infa):
    hlavy_frazi_veta_id = []
    hlavy_frazi_veta_form = []
    delky_klauzi = []

    hlavy_frazi_klauze_form = []

    slova_frazi_veta_form = []
    slova_frazi_veta_id = []

    for hlava_klauze in veta_info["predikáty id"]:
        fraze_klauze_id, fraze_klauze_form  = hledani_frazi(poradi_vety, hlava_klauze, veta_info["predikáty id"])
        hlavy_frazi_veta_id.append(fraze_klauze_id)
        hlavy_frazi_veta_form.append(fraze_klauze_form)

    veta_info["hlavy frází form"] = hlavy_frazi_veta_form
    veta_info["hlavy frází id"] = hlavy_frazi_veta_id
    
    for klauze in veta_info["hlavy frází id"]:
        delka_klauze = len(klauze)
        delky_klauzi.append(delka_klauze)
    veta_info["délky klauzí"] = delky_klauzi


    # information about clauses
    for poradi, predikat in enumerate(veta_info["predikáty id"]):
        veta_info["klauze infa"].append({"klauze číslo": poradi})
        #veta_info["klauze infa"][poradi]["klauze hlavy frází"] = veta_info["hlavy frází form"][poradi]
        veta_info["klauze infa"][poradi]["délka klauze ve frázích"] = len(veta_info["hlavy frází form"][poradi])

        slova_frazi_klauze_form = []
        slova_frazi_klauze_id = []

        for hlava_fraze_form, hlava_fraze_id in enumerate(veta_info["hlavy frází id"][poradi]):
            slova_fraze_id = [hlava_fraze_id]
            slova_fraze_form = [veta_info["hlavy frází form"][poradi][hlava_fraze_form]]
            hledani_slov_frazi(poradi_vety, [hlava_fraze_id], veta_info["predikáty id"])
            slova_frazi_klauze_form.append(slova_fraze_form)
            slova_frazi_klauze_id.append(slova_fraze_id)

            fraze_slova.append(slova_fraze_form)



        slova_frazi_veta_form.append(slova_frazi_klauze_form)
        slova_frazi_veta_id.append(slova_frazi_klauze_id)


        delka_frazi = []
        for klauze in slova_frazi_veta_form:
            delka_frazi_klauze = []
            for fraze in klauze:
                delka_frazi_klauze.append(len(fraze))
            delka_frazi.append(delka_frazi_klauze)
        
    for poradi, predikat in enumerate(veta_info["predikáty id"]):
        veta_info["klauze infa"][poradi]["slova frází form"] = slova_frazi_veta_form[poradi]
        veta_info["klauze infa"][poradi]["slova frází id"] = slova_frazi_veta_id[poradi]
        veta_info["klauze infa"][poradi]["délka frází ve slovech"] = delka_frazi[poradi]
        

# uložení do souboru
vety_infa_text = ""
for polozka in vety_infa:
    vety_infa_text = vety_infa_text + pformat(polozka) + "\n\n"

# saving the words of each phrase (including the phrase head)
with open(OUTPUT_FILE, "w", encoding="UTF-8") as file:
    for polozka in fraze_slova:
        file.write(" ".join(polozka) + "\n\n")