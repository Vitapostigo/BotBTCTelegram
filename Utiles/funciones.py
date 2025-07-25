import re
import bitcoinrpc
import requests
from bitcoinrpc.authproxy import AuthServiceProxy,JSONRPCException
from datetime import datetime
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
def precioPorBTC(num):
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()

    valorEnDols = (data['bitcoin']['usd'])*num
    precio = "{:.2f}".format(valorEnDols)

    return str(precio)+ '$'
##########################################################
def numBloquesRed(user_id):
    redActual = booleanFromUser(user_id)

    if redActual == "Error":
        return redActual

    if redActual: 
        client = AuthServiceProxy(getTestnetClient())
    else:
        client = AuthServiceProxy(getMainnetClient())

    try: 
        jsonToParse = client.getblockchaininfo()
    except: 
        return "Error de conexión"  
     
    resultadoRed = jsonToParse.get("chain", "Desconocido") 

    return int(jsonToParse["blocks"])

##########################################################
def infoBlockchain(user_id):
    redActual = booleanFromUser(user_id)

    if redActual == "Error":
        return redActual

    if redActual: 
        client = AuthServiceProxy(getTestnetClient())
    else:
        client = AuthServiceProxy(getMainnetClient())

    try: 
        jsonToParse = client.getblockchaininfo()
    except: 
        return "Error de conexión"  
     
    resultadoRed = jsonToParse.get("chain", "Desconocido") 
    
    if resultadoRed == "main":
        redInfo = "mainnet"
    elif resultadoRed == "test":
        redInfo = "testnet"
    else:
        return "Problema con la red."

    fecha_hora = datetime.utcfromtimestamp(jsonToParse["time"])

    bytesEnGB = 1024*1024*1024
    

    retorno = "Información actual sobre la red:\nRed actual: " + redInfo + "\nNúmero de bloques: " + str(jsonToParse["blocks"]) + "\nDificultad actual de la red: " + str(jsonToParse["difficulty"]) + "\
    \nHora UTC registrada: " +  str(fecha_hora) + "\nEspacio en disco: " + str(jsonToParse["size_on_disk"]/bytesEnGB) + " GB."
    
    return retorno
##########################################################
def textoMultisig(dirsConvencionales,dirsMultisig):
    textoRetorno = ""
    if len(dirsConvencionales) != 0:
        textoRetorno = "Direcciones no multisig:\n"
        for i in range(0, len(dirsConvencionales), 2):
            textoRetorno += dirsConvencionales[i] + " ha recibido: " + str(dirsConvencionales[i+1]) + "\n"

    #Direcciones multisig:
    textoRetorno = "Direcciones multisig:\n"
    for i in range(0, len(dirsMultisig), 2):
        multiSigActual = dirsMultisig[i].split()
        textoRetorno += f"La una multisig {multiSigActual[0]}/{multiSigActual[len(multiSigActual)-2]} ha recibido: {str(dirsMultisig[i+1])}\n"
        textoRetorno += "Y está compuesta por las siguientes claves públicas:\n"
        for j in range(1, len(multiSigActual)-2, 1):
            textoRetorno += multiSigActual[j] + "\n"

    return textoRetorno
##########################################################
def check_multisig(transaction):
    for output in transaction['vout']:
        script_asm = output['scriptPubKey']['asm']
        if 'OP_CHECKMULTISIG' in script_asm:
            return True
    return False
##########################################################
def printInputsFromList(list):
    retorno = ""
    for address in list:
        retorno += f"{address}\n"
    return retorno
##########################################################
def outputFormat(list):
    retorno = ""
    for salida in list:
        #Caso OP_RETURN
        if salida[0] == 'OP_RETURN':
            if len(salida[0].split()) == 1:
                datosHex = salida[1]
            else:
                datosHex = salida[1].split()[1]
            retorno += f"Dirección: OP_RETURN, datos escritos en hex: {datosHex}\n"
            try:
                asciival = bytearray.fromhex(datosHex).decode()
                retorno += f"Valor en ASCII: {asciival}\n"
            except UnicodeDecodeError:
                retorno += "El cual no tiene representación ASCII\n"
        else:
            #Caso dirección standard
            retorno += f"Dirección: {salida[0]} recibió: {salida[1]} BTC\n"
        
    return retorno
##########################################################
def infoTx(user_id,tx):
    #1 entrada 1 salida:             tx=c9435711f75903656f0b04d84b4058f2755403aa279774de212f75797c04474f
    #1 entrada varias salidas:       tx=973eaa563475eaa3291612811c0348b260823a4b790f03eaa1a5ae52fa717804
    #varias entradas varias salidas: tx=7274c3d4a3dd41806fa2f56bcccee5495b61d24f796fed3024502d6f231f7c73
    #Multisig entrada:               tx=eeab3ef6cbea5f812b1bb8b8270a163b781eb7cde10ae5a7d8a3f452a57dca93
    #Multisig salida:                tx=d63667e49701df10b51dfe347e6ed6f59a73f4ef3c883ad9cfee3d23064372a6
    #OP_RETURN:                      tx=ea510170d41e31872f919d9af0123d843481c0d5f2560609d565d515419acc59
    #OP_RETURN_ASCII:                tx=8bae12b5f4c088d940733dcd1455efc6a3a69cf9340e17a981286d3778615684
    #COINBASE:                       tx=89e0d6f560f0de732f3ad46d928582802b77e693900e708b882ef913c7172172
    redActual = booleanFromUser(user_id)

    if redActual == "Error":
        return redActual

    if redActual: 
        client = AuthServiceProxy(getTestnetClient())
    else:
        client = AuthServiceProxy(getMainnetClient())
    
    validHash = bool(re.fullmatch(r'[0-9a-f]{64}', tx))

    if validHash:
        try:
            jsonTx = client.getrawtransaction(tx, True)
        except Exception as data:
            return "Error obteniendo la transacción, revise los datos."
    else:
        return "El hash de la transacción proporcionada no es válido."

    try:
        if "coinbase" in jsonTx["vin"][0]:
            id = jsonTx["txid"]
            recompensa = float(jsonTx["vout"][0]["value"])
            direccion_minero = jsonTx["vout"][0]["scriptPubKey"].get("address", "Desconocida")
            bloque_id = jsonTx.get("blockhash", "Desconocido")
            return (
                f"La transacción con id: {id} es una transacción de tipo coinbase.\n"
                f"Corresponde a la minería de un bloque con una recompensa de {recompensa:.8f} BTC que en este momento tienen un valor de: {precioPorBTC(recompensa)}\n"
                f"El beneficiario (minero) es: {direccion_minero}\n"
                f"ID del bloque minado: {bloque_id}"
            )
        # Obtener los inputs
        dirsEntrada = []
        for vin in jsonTx["vin"]:
            prev_tx = client.getrawtransaction(vin["txid"], True)
            vout = prev_tx["vout"][vin["vout"]]
            dirsEntrada.append(vout["scriptPubKey"]["address"])

        if not check_multisig(jsonTx):  # En caso de que sea una transacción sin salida multisig procesamos aquí
            dirsSalidaSaldo = []
            for vout in jsonTx['vout']:
                ###Si tenemos un OP_RETURN los campos cambian, tratamos de forma diferente.
                if 'OP_RETURN' in vout['scriptPubKey']['asm']:
                    # Si es OP_RETURN, extraemos los datos
                    data = vout['scriptPubKey']['asm'].split(' ', 1)[1] if len(vout['scriptPubKey']['asm'].split(' ', 1)) > 1 else "No data"
                    dirsSalidaSaldo.append(("OP_RETURN", data))
                else:
                    # Si no es OP_RETURN, procesamos como antes
                    dirsSalidaSaldo.append((vout['scriptPubKey'].get('address', 'Desconocida'), float(vout['value'])))
    
            suma_total = sum(valor for _, valor in dirsSalidaSaldo if isinstance(valor, float))
            return f"En la transacción con id: {tx}\nha habido un movimiento de fondos por valor de: {suma_total} BTC, valorado en: {precioPorBTC(suma_total)} actualmente.\nHa sido enviada por las siguientes direccion/es:\n{printInputsFromList(dirsEntrada)}y la/s salida/s son:\n{outputFormat(dirsSalidaSaldo)}"

        else:#Tratar el procesamiento de la multisig
            dirsConvencionales = []
            dirsMultisig = []
            suma_total = 0
            #Direcciones normales
            for output in jsonTx.get('vout', []):
                address = output.get('scriptPubKey', {}).get('address')
                if address:
                    dirsConvencionales.append(address)
                    dirsConvencionales.append(output.get('value'))        #<addr1> <value1> <addr2> <value2> ... <addrn> <valuen>
                    suma_total += output.get('value')

            #Multisig
            for output in jsonTx['vout']:
                script_asm = output['scriptPubKey']['asm']
                if 'OP_CHECKMULTISIG' in script_asm:
                    dirsMultisig.append(script_asm)
                    dirsMultisig.append(output.get('value'))
                    suma_total += output.get('value')

            return f"En la transacción con id: {tx}\nse han movido fondos por valor de: {suma_total} BTC, valorado en: {precioPorBTC(suma_total)} actualmente.\nHa sido enviada por las siguientes direccion/es:\n{printInputsFromList(dirsEntrada)}Y la/s salida/s se estructuran de la siguiente manera:\n" + textoMultisig(dirsConvencionales,dirsMultisig)
    except KeyError as ke:
        if redActual: #Testnet
            return f"Transacción con scripts complejos. Para poder obtener más información visita:\nhttps://blockstream.info/testnet/tx/{tx}/"
        else:
            return f"Transacción con scripts complejos. Para poder obtener más información visita:\nhttps://www.blockchain.com/explorer/transactions/btc/{tx}/"
    except Exception as excp:
        print(jsonTx)
        return f"Caso solo para debug, no debería darse.\n{excp}"
##########################################################
def blockInfo(user_id, data):
    from consultasFulcrum import getBlockFromTx
    resultadoBloque = getBlockFromTx(user_id, data)
    isBlockHash = True
    retorno = ""

    blockHash = data

    if not isinstance(resultadoBloque,str) and resultadoBloque is not None:
        retorno += f"La transacción: {data} está contenida en:\n"
        blockHash = resultadoBloque["result"]["block_hash"]
        isBlockHash = False

    redActual = booleanFromUser(user_id)

    if redActual == "Error":
        return redActual

    if redActual: 
        client = AuthServiceProxy(getTestnetClient())
    else:
        client = AuthServiceProxy(getMainnetClient())

    try:
        numberData = int(data)
        if len(str(data)) != 64:
            if numberData > numBloquesRed(user_id): 
                return "El bloque solicitado supera la altura de la red."
            blockHash = client.getblockhash(numberData)
    except ValueError:
        if isBlockHash:
            blockHash = data

    try:
        blockstats = client.getblockstats(blockHash)
    except bitcoinrpc.authproxy.JSONRPCException:
        return "Error, no se ha podido encontrar el bloque, revisa que los datos sean correctos..."
    except Exception as e:
        return "Error de conexión con el servidor."

    try: 
        satsInBTC = 100000000
        retorno += f"Hash del bloque: {blockstats['blockhash']}\nCon altura: {blockstats['height']}\nComisión promedio: {blockstats['avgfee']} satoshis\nComisión por byte: {blockstats['avgfeerate']} sats/byte\n"
        retorno += f"Minado en {datetime.utcfromtimestamp(blockstats['time'])}\nHay un total de {blockstats['txs']} transacciones con {numBloquesRed(user_id)-blockstats['height']} confirmaciones\nRecompensa del minero: {blockstats['subsidy']/satsInBTC} BTC\n"
        retorno += f"Hay transacciones por un valor total de: {blockstats['total_out']/satsInBTC} que, en este momento tienen un valor de: {precioPorBTC(blockstats['total_out']/satsInBTC)}\n"
        retorno += f"Máxima comisión pagada en el bloque: {blockstats['maxfee']} satoshis\nMáxima comisión por byte: {blockstats['maxfee']} sats/byte\nMínima comisión pagada en el bloque: {blockstats['minfee']} satoshis\nMínima comisión por byte: {blockstats['maxfee']} sats/byte\n"
        retorno += f"Menor transacción del bloque: {blockstats['mintxsize']} bytes\nMáxima transacción del bloque: {blockstats['maxtxsize']} bytes\nPeso completo del bloque: {blockstats['total_size']/1024} kB"
    except: 
        return "Error obteniendo información del bloque."

    return retorno