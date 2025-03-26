import requests
import re
from bitcoinrpc.authproxy import AuthServiceProxy
#from decimal import Decimal
#Imports propios
from conexionMongo import booleanFromUser
from credentials import *

##########################################################
def precio_bitcoin():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    return str(data['bitcoin']['usd'])
##########################################################
def isValidBTCAddress(address):
    regex = r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{24,39}$"
    return bool(re.match(regex, address))
##########################################################
def precioPorBTC(num):
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()

    valorEnDols = (data['bitcoin']['usd'])*num
    precio = "{:.2f}".format(valorEnDols)

    return str(precio)+ '$'

##########################################################
def infoBlockchain(user_id):
    redActual = booleanFromUser(user_id)

    if redActual == "Error":
        return redActual

    if redActual: 
        client = AuthServiceProxy(getTestnetClient())
    else:
        client = AuthServiceProxy(getMainnetClient())

    jsonToParse = client.getblockchaininfo()
    resultadoRed = jsonToParse.get("chain", "Desconocido")

    if resultadoRed == "main":
        return "mainnet"
    elif resultadoRed == "test":
        return "testnet"
    else:
        return "undefined"
##########################################################
def infoTx(user_id,tx):
    #Solo ajustar la salida para el bot.
    #1 entrada 1 salida:             tx=c9435711f75903656f0b04d84b4058f2755403aa279774de212f75797c04474f
    #1 entrada varias salidas:       tx=973eaa563475eaa3291612811c0348b260823a4b790f03eaa1a5ae52fa717804
    #varias entradas varias salidas: tx=7274c3d4a3dd41806fa2f56bcccee5495b61d24f796fed3024502d6f231f7c73
    redActual = booleanFromUser(user_id)

    if redActual == "Error":
        return redActual

    if redActual: 
        client = AuthServiceProxy(getTestnetClient())
    else:
        client = AuthServiceProxy(getMainnetClient())
    
    jsonTx = client.getrawtransaction(tx, True)

    # Obtener los inputs
    dirsEntrada = []
    for vin in jsonTx["vin"]:
        prev_tx = client.getrawtransaction(vin["txid"], True)
        vout = prev_tx["vout"][vin["vout"]]
        dirsEntrada.append(vout["scriptPubKey"]["address"])

    dirsSalidaSaldo = [(vout['scriptPubKey']['address'], float(vout['value'])) for vout in jsonTx['vout']]

    suma_total = sum(valor for _, valor in dirsSalidaSaldo)
    
    stringRetorno = "La transacción con id: " + str(tx) + " tiene un valor total de: " + str(suma_total) + " BTC, valorado en: " + precioPorBTC(suma_total) + " actualmente\n \
    ha sido enviada por las siguientes direccion/es:\n " + str(dirsEntrada) + "\ny la/s salida/s son:\n" + str(dirsSalidaSaldo)
    return stringRetorno
##########################################################
