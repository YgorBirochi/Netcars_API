from flask import Flask, request, jsonify, make_response
from main import app, con, senha_secreta
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import jwt
from gerar_pix import *

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

    cursor = con.cursor()

    cursor.execute('SELECT 1 FROM FINANCIAMENTO WHERE ID_USUARIO = ?', (id_usuario,))

    if cursor.fetchone():
        return jsonify({'error': 'Você já possui um parcelamento em andamento.'}), 400

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

        if tipo_veic == 1:
            cursor.execute('UPDATE CARROS SET ATIVO = 0 WHERE ID_CARRO = ?', (id_veic,))
        else:
            cursor.execute('UPDATE MOTOS SET ATIVO = 0 WHERE ID_MOTO = ?', (id_veic,))

        con.commit()

        return jsonify({'success': 'Seu parcelamento foi gerado com sucesso!'}), 200

    except Exception as e:
        con.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/buscar_financiamento', methods=['GET'])
def buscar_financiamento():
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

    cursor = con.cursor()

    try:
        cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                'error': 'Usuário não encontrado.'
            }), 400

        tipo_usuario = user[0]

        if tipo_usuario in [1, 2]:
            cursor.execute("SELECT ID_FINANCIAMENTO FROM FINANCIAMENTO")
            data_financiamento = cursor.fetchall()

            if not data_financiamento:
                return jsonify({
                    'total': 0,
                    'concluidos': 0,
                    'em_andamento': 0
                }), 200

            lista_ids_financ = [row[0] for row in data_financiamento]

            em_andamento = 0
            concluidos = 0

            for id_financ in lista_ids_financ:
                cursor.execute('''
                        SELECT 1 FROM FINANCIAMENTO_PARCELA
                        WHERE ID_FINANCIAMENTO = ?
                        AND STATUS NOT IN (3,4)
                    ''', (id_financ,))

                pendente = cursor.fetchone()

                if pendente:
                    em_andamento += 1
                else:
                    concluidos += 1

            return jsonify({
                'total': len(lista_ids_financ),
                'concluidos': concluidos,
                'em_andamento': em_andamento
            }), 200

        else:
            cursor.execute('''
                        SELECT ID_FINANCIAMENTO
                        FROM FINANCIAMENTO
                        WHERE ID_USUARIO = ?
                    ''', (id_usuario,))

            result_id_financiamento = cursor.fetchall()

            if not result_id_financiamento:
                return jsonify({'error': 'Nenhum financiamento encontrado.'}), 400

            lista_ids_financiamento = [row[0] for row in result_id_financiamento]

            for id_financiamento in lista_ids_financiamento:
                cursor.execute('''
                        SELECT 1 FROM FINANCIAMENTO_PARCELA
                        WHERE ID_FINANCIAMENTO = ?
                        AND STATUS NOT IN (3,4)
                    ''', (id_financiamento,))

                pendente = cursor.fetchone()

                if not pendente:
                    continue

                cursor.execute('''
                        SELECT ENTRADA, QNT_PARCELAS, TIPO_VEICULO, ID_VEICULO, VALOR_TOTAL 
                        FROM FINANCIAMENTO WHERE ID_FINANCIAMENTO = ?
                    ''', (id_financiamento,))

                data_financiamento = cursor.fetchall()

                if not data_financiamento:
                    return jsonify({'error': 'Nenhnum financiamento encontrado.'}), 400

                entrada = data_financiamento[0][0]
                qnt_parcelas = data_financiamento[0][1]
                tipo_veiculo = data_financiamento[0][2]
                id_veiculo = data_financiamento[0][3]
                valor_total = data_financiamento[0][4]

                cursor.execute('''
                        SELECT NUM_PARCELA, VALOR_PARCELA, VALOR_PARCELA_AMORTIZADA, DATA_VENCIMENTO, DATA_PAGAMENTO, STATUS 
                        FROM FINANCIAMENTO_PARCELA WHERE ID_FINANCIAMENTO = ? ORDER BY DATA_VENCIMENTO ASC
                    ''', (id_financiamento,))

                data_parcelas = cursor.fetchall()

                lista_parcelas = []
                for parcela in data_parcelas:
                    info = {
                        "num_parcela": parcela[0],
                        "valor_parcela": parcela[1],
                        "valor_parcela_amortizada": parcela[2],
                        "data_vencimento": parcela[3],
                        "data_pagamento": parcela[4],
                        "status": parcela[5]
                    }

                    lista_parcelas.append(info)

                if tipo_veiculo == 1:
                    cursor.execute(
                        "SELECT MARCA, MODELO, ANO_FABRICACAO, ANO_MODELO, VERSAO FROM CARROS WHERE ID_CARRO = ?",
                        (id_veiculo,))

                    dados_veiculo = cursor.fetchall()[0]

                    json_veiculo = {
                        "id_veiculo": id_veiculo,
                        "tipo_veiculo": tipo_veiculo,
                        "marca": dados_veiculo[0],
                        "modelo": dados_veiculo[1],
                        "ano_fabricacao": dados_veiculo[2],
                        "ano_modelo": dados_veiculo[3],
                        "versao": dados_veiculo[4]
                    }
                else:
                    cursor.execute("SELECT MARCA, MODELO, ANO_FABRICACAO, ANO_MODELO FROM MOTOS WHERE ID_MOTO = ?",
                                   (id_veiculo,))

                    dados_veiculo = cursor.fetchall()[0]

                    json_veiculo = {
                        "id_veiculo": id_veiculo,
                        "tipo_veiculo": tipo_veiculo,
                        "marca": dados_veiculo[0],
                        "modelo": dados_veiculo[1],
                        "ano_fabricacao": dados_veiculo[2],
                        "ano_modelo": dados_veiculo[3]
                    }

                return jsonify({
                    "entrada": entrada,
                    "qnt_parcelas": qnt_parcelas,
                    "valor_total": valor_total,
                    "lista_parcelas": lista_parcelas,
                    "dados_veiculo": json_veiculo
                })
    finally:
        cursor.close()

@app.route('/gerar_qrcode_parcela/<tipo>', methods=['GET'])
def gerar_qrcode_parcela_atual(tipo):
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

    cursor = con.cursor()

    cursor.execute('SELECT ID_FINANCIAMENTO FROM FINANCIAMENTO WHERE ID_USUARIO = ?', (id_usuario,))

    result_financ = cursor.fetchone()

    if not result_financ:
        return jsonify({'error': 'Nenhum financiamento encontrado.'}), 400

    id_financiamento = result_financ[0]

    if tipo == 'recente':
        cursor.execute('''
            SELECT FIRST 1
               ID_FINANCIAMENTO_PARCELA,
               VALOR_PARCELA,
               DATA_VENCIMENTO
            FROM FINANCIAMENTO_PARCELA
            WHERE ID_FINANCIAMENTO = ?
            AND STATUS NOT IN (3, 4)
            ORDER BY DATA_VENCIMENTO ASC;
        ''', (id_financiamento,))
    elif tipo == 'amortizar':
        cursor.execute('''
                SELECT FIRST 1
                   ID_FINANCIAMENTO_PARCELA,
                   VALOR_PARCELA_AMORTIZADA,
                   DATA_VENCIMENTO
                FROM FINANCIAMENTO_PARCELA
                WHERE ID_FINANCIAMENTO = ?
                AND STATUS NOT IN (3, 4)
                ORDER BY DATA_VENCIMENTO DESC;
            ''', (id_financiamento,))
    else:
        return jsonify({'error': 'Parâmetro inválido.'}), 400

    result_parc = cursor.fetchone()

    if not result_parc:
        return jsonify({'error': 'Nenhuma parcela encontrada'})

    id_parcela = int(result_parc[0])
    valor_parcela = float(result_parc[1])
    data_vencimento = result_parc[2]

    data_atual = datetime.now()

    # Aplica juros de 1% ao dia em caso de atraso
    if isinstance(data_vencimento, str):
        data_vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d")  # ajuste o formato se necessário

    juros = 0
    if data_atual > data_vencimento:
        dias_atraso = (data_atual - data_vencimento).days

        # Calcula o valor da parcela com juros
        valor_parcela_juros = valor_parcela * (1 + JUROS) ** dias_atraso

        # Obtém os juros
        juros = valor_parcela_juros - valor_parcela

        # Substitui o valor da parcela
        valor_parcela = valor_parcela_juros

    cursor.execute("SELECT cg.RAZAO_SOCIAL, cg.CHAVE_PIX, cg.CIDADE FROM CONFIG_GARAGEM cg")
    resultado = cursor.fetchone()

    if not resultado:
        return jsonify({"erro": "Chave pix não encontrada"}), 404

    nome, chave_pix, cidade = resultado

    payload, link, nome_arquivo = gerar_pix_funcao(nome, valor_parcela, chave_pix, cidade)

    caminho = os.path.join(os.getcwd(), "upload", "qrcodes", nome_arquivo)

    response = make_response(send_file(
        caminho,
        mimetype='image/png',
        as_attachment=True,
        download_name=nome_arquivo
    ))
    response.headers['ID-PARCELA'] = str(id_parcela)
    response.headers['VALOR-PARCELA'] = str(valor_parcela)
    response.headers['JUROS'] = str(juros)

    response.headers['Access-Control-Expose-Headers'] = 'ID-PARCELA, VALOR-PARCELA, JUROS'

    return response

@app.route('/pagar_parcela/<int:id_parcela>/<int:amortizada>', methods = ['GET'])
def pagar_parcela(id_parcela, amortizada):
    if id_parcela is None or amortizada is None or amortizada not in [0, 1]:
        return jsonify({'error': 'Dados incorretos.'}), 400

    cursor = con.cursor()

    cursor.execute('SELECT VALOR_PARCELA, DATA_VENCIMENTO FROM FINANCIAMENTO_PARCELA WHERE ID_FINANCIAMENTO_PARCELA = ?', (id_parcela,))

    result_parc = cursor.fetchone()

    if not result_parc:
        return jsonify({'error': 'Parcela não encontrada.'}), 400

    valor_parcela = float(result_parc[0])
    data_vencimento = result_parc[1]

    data_atual = datetime.now()

    # Aplica juros de 1% ao dia em caso de atraso
    if isinstance(data_vencimento, str):
        data_vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d")  # ajuste o formato se necessário

    if data_atual > data_vencimento:
        dias_atraso = (data_atual - data_vencimento).days

        # Calcula o valor da parcela com juros
        valor_parcela = valor_parcela * (1 + JUROS) ** dias_atraso

        cursor.execute('''
                        UPDATE FINANCIAMENTO_PARCELA
                        SET VALOR_PARCELA = ?
                        WHERE ID_FINANCIAMENTO_PARCELA = ?
                    ''', (valor_parcela, id_parcela,))

    try:
        if amortizada == 0:
            cursor.execute('''
                UPDATE FINANCIAMENTO_PARCELA SET STATUS = 3,
                DATA_PAGAMENTO = CURRENT_TIMESTAMP 
                WHERE ID_FINANCIAMENTO_PARCELA = ?
            ''', (id_parcela,))
        else:
            cursor.execute('''
                UPDATE FINANCIAMENTO_PARCELA SET STATUS = 4,
                DATA_PAGAMENTO = CURRENT_TIMESTAMP 
                WHERE ID_FINANCIAMENTO_PARCELA = ?
            ''', (id_parcela,))

        cursor.execute('''
            SELECT ID_FINANCIAMENTO
            FROM FINANCIAMENTO_PARCELA
            WHERE ID_FINANCIAMENTO_PARCELA = ?
        ''', (id_parcela,))

        id_financiamento = cursor.fetchone()[0]

        cursor.execute('''
            SELECT 1 FROM FINANCIAMENTO_PARCELA
            WHERE ID_FINANCIAMENTO = ?
            AND STATUS NOT IN (3,4)
        ''', (id_financiamento,))

        pendente = cursor.fetchone()

        if not pendente:
            cursor.execute('''
                UPDATE VENDA_COMPRA
                SET STATUS = 2
                WHERE ID_FINANCIAMENTO = ?
            ''', (id_financiamento,))

        con.commit()

        if amortizada == 0:
            return jsonify({'success': 'Parcela paga com sucesso!'}), 200
        else:
            return jsonify({'success': 'Parcela amortizada com sucesso!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
