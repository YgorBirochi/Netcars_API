from flask import Flask, request, jsonify
from main import app, con, senha_secreta
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import jwt

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

JUROS = 0.01 # Juros de 1%

def calcular_financiamento(id_veic, tipo_veic, qnt_parcelas, entrada):
    cursor = con.cursor()

    if tipo_veic == 1:
        cursor.execute('SELECT PRECO_VENDA FROM CARROS WHERE ID_CARRO = ?', (id_veic,))
    elif tipo_veic == 2:
        cursor.execute('SELECT PRECO_VENDA FROM MOTOS WHERE ID_MOTO = ?', (id_veic,))
    else:
        return jsonify({
            'error': 'Tipo de veículo inválido.'
        }), 400

    resposta_veic = cursor.fetchone()

    if not resposta_veic:
        return jsonify({'error': 'Veículo não encontrado'}), 400

    preco_venda = float(resposta_veic[0])

    if entrada >= preco_venda:
        return jsonify({
            'qnt_parcelas': 0,
            'entrada': entrada,
            'preco_venda': preco_venda
        }), 200

    preco_sem_entrada = preco_venda - entrada

    parcela_inicial = preco_sem_entrada / qnt_parcelas

    lista_parcelas = {}

    data_inicial = datetime.now()

    for i in range(qnt_parcelas):
        num_parcela = i + 1

        parcela_nova = parcela_inicial * (1 + JUROS)**num_parcela

        data_pagamento = (data_inicial + relativedelta(months=+num_parcela)).strftime('%Y-%m-%d')

        lista_parcelas[num_parcela] = {
                                        'valor': round(parcela_nova, 2),
                                        'valor_amortizado': round(parcela_inicial, 2),
                                        'data': data_pagamento
                                      }

    soma_parcelas = 0
    for j in range(len(lista_parcelas)):
        soma_parcelas += lista_parcelas[j+1]['valor']

    valor_total = soma_parcelas + entrada

    return jsonify({
        'valor_total': valor_total,
        'lista_parcelas': lista_parcelas,
        'qnt_parcelas': qnt_parcelas,
        'entrada': entrada,
        'preco_venda': preco_venda
    }), 200

@app.route('/financiamento/<int:id_veic>/<int:tipo_veic>/<int:qnt_parcelas>/<float:entrada>', methods=['GET'])
def obter_parcelas_financiamento(id_veic, tipo_veic, qnt_parcelas, entrada):
    # Caso não tenha enviado os dados
    if id_veic is None or tipo_veic is None or qnt_parcelas is None or entrada is None:
        return jsonify({
            'error': 'Dados incompletos.'
        }), 400
    # Retorna a resposta da função
    return calcular_financiamento(id_veic, tipo_veic, qnt_parcelas, entrada)

@app.route('/financiamento', methods=['POST'])
def financiamento():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)
    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    data = request.get_json()

    # Dados recebidos
    id_veic = data.get('id_veiculo')
    tipo_veic = data.get('tipo_veiculo')
    qnt_parcelas = data.get('qnt_parcelas')
    entrada = data.get('entrada')

    if entrada is None or qnt_parcelas is None or id_veic is None or tipo_veic is None:
        return jsonify({'error': 'Dados incompletos'}),400

    # Separando a resposta e o status
    response_obj, status_code = calcular_financiamento(id_veic, tipo_veic, qnt_parcelas, entrada)
    dados = response_obj.get_json()

    if status_code != 200:
        return response_obj, status_code

    valor_total = dados.get('valor_total')
    lista_parcelas = dados.get('lista_parcelas')

    try:
        cursor = con.cursor()

        cursor.execute('''
            INSERT INTO FINANCIAMENTO
            (ID_USUARIO, VALOR_TOTAL, ENTRADA, QNT_PARCELAS, TIPO_VEICULO, ID_VEICULO)
            VALUES(?, ?, ?, ?, ?, ?) RETURNING ID_FINANCIAMENTO
        ''', (id_usuario, valor_total, entrada, qnt_parcelas, tipo_veic, id_veic))

        id_financiamento = cursor.fetchone()[0]

        # Depois de extrair valor_total e lista_parcelas...
        for num_parcela, parcela in lista_parcelas.items():
            cursor.execute(
                '''
                INSERT INTO FINANCIAMENTO_PARCELA
                  (ID_FINANCIAMENTO, NUM_PARCELA, VALOR_PARCELA,
                   VALOR_PARCELA_AMORTIZADA, DATA_VENCIMENTO, STATUS)
                VALUES(?, ?, ?, ?, ?, 1)
                ''',
                (
                    id_financiamento,
                    num_parcela,
                    parcela.get('valor'),
                    parcela.get('valor_amortizado'),
                    parcela.get('data')
                )
            )

        con.commit()

        return jsonify({'success': 'Seu parcelamento foi gerado com sucesso! Veja mais detalhes na seção "financiamento".'}), 200

    except Exception as e:
        con.rollback()
        return jsonify({'error': str(e)}), 400
