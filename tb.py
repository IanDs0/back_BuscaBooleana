from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer
from glob import glob

import unidecode
import re
import json

import matplotlib.pyplot as plt
import numpy as np


def read_html(filename):
    # leitura do html
    with open(filename, encoding='iso-8859-1') as html_file:
        html = html_file.read()
    # parser com beautifulsoup
    soup = BeautifulSoup(html)
    # Buscar bloco de texto nos htmls
    text_list = soup.find('body')#.findChildren('font')[2]
    # extrair o texto de cada tag <p>
    
    text_list = [re.sub(r'[^\w\s]|([0-9]*\,[0-9]+|[0-9]+)', '', 
    unidecode.unidecode(x.text)) for x in text_list if x.text]

    return text_list

def count_words(text):
    word_count = {}
    # instanciação de biblioteca de contagem de palavras
    vec = CountVectorizer()
    # cria uma matriz de contagem de palavras por documentos
    X = vec.fit_transform(text)
    # extrai o vocabulário de todos os documentos
    vocab = vec.get_feature_names_out()

    # para cada palavra no covabulario extrai a soma de sua contagem em todos os documentos
    for count, word in zip(X.sum(axis=0).tolist()[0], vocab):
        word_count[word] = count

    # Ordena o dicionário de palavras pela contagem
    word_count = {k: v for k, v in sorted(word_count.items(), key=lambda item: item[1], reverse=True)}
    return word_count

text_list = []
allPalavras = []
nameArquivos = []
for file in glob('./CRPC sub-corpus oral espontÉneo/*'):
    nameArquivos.append(file)
    if file.split('\\')[-1].startswith('pf'):
        data = read_html(file)
        contPalavra = count_words(data)
        
        allPalavras.extend(contPalavra)
        text_list.append(contPalavra)

allPalavras = sorted(set(allPalavras))
allPalavras.pop(0)

dict = {}

for i in range(len(text_list)):
    testa = []

    for j in text_list[i].keys():
        testa.append(j)

    for item in allPalavras: 
        if item in testa:
            # print(item)
            if item not in dict: 
                dict[item] = []
            if item in dict: 
                dict[item].append(i)

with open('word_index.json', 'w') as jfile:
    json.dump(dict, jfile, indent=4)

def Busca(text):
    aux = []
    aux = dict[text]

    return aux

def Operadores(text):
    
    result = []


    if text.find('+')>0:
        perquisa = text.split("+")

        i=0

        for palavra in perquisa:
            if i !=0:
                result = result.intersection(Busca(palavra))
            else:
                i=1
                result = set(Busca(palavra))

        return result

    elif text.find('-')>0:
        perquisa = text.split("-")

        i=0

        for palavra in perquisa:
            if i !=0:
                result = result.difference(Busca(palavra))
            else:
                i=1
                result = set(Busca(palavra))

        return result

    elif text.find('|')>0:

        perquisa = text.split("|")

        for palavra in perquisa:
            result.extend(Busca(palavra))
            
        return sorted(set(result))

    else:

        return [-1]

class Buscar(BaseModel):
    busca: str

def Json (retorno):
    retornando = retorno.split("\\")
    return{
        "nome": retornando[-1],
        "diretorio": retorno
    }

app = FastAPI()

origins = ['http://localhost:3000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/teste")
def read_root(busca: Buscar):
    res=Operadores(busca.busca.lower())
    res = list(res)

    if res[0] != -1:
        retorno = []
        for r in res:
            retorno.append(Json(nameArquivos[int(r+2)]))

        return {"results": retorno}
    else:
        return {"Status": 404, "Mensagem":"Sem Resultados"}