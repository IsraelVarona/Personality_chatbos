import csv
import os
import openai
from dotenv import load_dotenv
from openai import OpenAI
from system_prompts import neutral_prompt             #ESCOGER PROMPT: neutral, Jiang, Israel
from system_prompts.my_prompt_neuroticism_negative import MY_PROMPT       #QUE PROMPT DE OSCAR IMPORTAR

load_dotenv()

#label_raw,text,label_ocean,key

client = OpenAI(api_key=os.getenv("API_KEY"))
system_prompt = neutral_prompt.description["prompt"]       #CON QUE PROMPT CORRER EL TEST               
items = []
logs = [] #errores
prompt_and_answer = []

#Agrega cada uno de los ítems del mpi 120 a la lista 'items'
def get_items(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)    
        for row in reader:
            items.append(row)

#Itera sobre la lista 'items' y si el ítem pertenece al rasgo 'trait', lo agrega a la lista 'trait_items', la cual es devuelta
def get_trait_items(trait):
    trait_items = []
    for item in items:
        if item[2] == trait:
            trait_items.append(item)
    return trait_items

#Interactua con el chatbot. Da un prompt (system) y un mensaje del usuario (item). Regresa la respuesta
def callGPT(item_prompt):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": item_prompt}
        ],
        temperature = 0
    )
    return completion.choices[0].message.content

#Crea el ítem que se le presentará al chatbot
def prompt(item_text):
    return f"""
    Question:
    Given the statement: "You {item_text}."
    Please choose from the following options to identify how accurately this statement describes you.
    Options:
    (A). Very Accurate
    (B). Moderately Accurate
    (C). Neither Accurate Nor Inaccurate
    (D). Moderately Inaccurate
    (E). Very Inaccurate

    Answer:
"""

#Con base en la respuesta, regresa el valor cuantitativo equivalente
def calculate_score(answer, key):
    answer_dom = {"(A). Very Accurate" : 5,
                  "(B). Moderately Accurate" : 4,
                "(C). Neither Accurate Nor Inaccurate": 3,
                "(D). Moderately Inaccurate" : 2,
                "(E). Very Inaccurate" : 1
    }
 
    try:
        return answer_dom[answer] if key == 1 else 5 - answer_dom[answer] + 1
    except:
        print("ERROR: Se recibio una respuesta no esperada de chatGPT."
              + " La respuesta fue: " + answer)
         
#Regresa el valor obtenido por el chatbot en el rasgo
def ocean_score_for_trait(trait):
    items = get_trait_items(trait)
    accumulated_score = 0
    for item in items:
        item_text = item[1]
        item_key = item[3]
        prompt_text = prompt(item_text)
        answer = callGPT(prompt_text)
        score = calculate_score(answer, item_key)
        if score != None:
            accumulated_score += score
            prompt_and_answer.append(prompt_text + " " + answer)
        else:
            logs.append("ERROR: " + item_text + ". Respuesta de chatGPT: " + answer)
    return accumulated_score / len(items)

#Crea un archivo.txt, itera sobre cada miembro de la lista y lo escribe como una línea del archivo
def data_to_txt(filename, data):
    with open(filename, "a") as file:
        for item in data:
            file.write(str(item) + "\n")

def run():
    file_path = "mpi_120.csv"
    output_file_path = ""   #A QUE ARCHIVO SE DIRIGIRA EL RESULTADO DEL TEST (autor-RASGOYVALENCIA-modelo.txt)
    get_items(file_path)

    trait = ""                       #EL RASGO A EVALUAR (inicial mayúscula del rasgo)
    evaluation =[]
    evaluation.append({"trait": trait,
                           "score": ocean_score_for_trait(trait)
                           }
                        )
    data_to_txt("ocean-score-evaluations/" + output_file_path, evaluation)
    data_to_txt("logs/" + output_file_path, logs)
    data_to_txt("all-prompts-with-answers/" + output_file_path, prompt_and_answer)
        
run()
