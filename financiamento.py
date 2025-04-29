from flask import Flask, request, jsonify
from main import app, con
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

    preco_venda = float(cursor.fetchone()[0])

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
    data = request.get_json()

    # Dados recebidos
    id_usuario = data.get('id_usuario')
    id_carro = data.get('id_carro')
    id_moto = data.get('id_moto')  # será None se não existir
    n = int(data.get('numero_parcelas'))
    PV = float(data.get('valor_financiamento'))

    # Taxa fixa mensal (3,5%)
    i = 0.035

    # Cálculo da parcela fixa (Sistema Price)
    PMT = PV * (i * (1 + i) ** n) / ((1 + i) ** n - 1)

    # Pré-cálculo de juros e amortizações (Price)
    juros_list = []
    amort_list = []
    saldo = PV
    for _ in range(n):
        juros = saldo * i
        amort = PMT - juros
        juros_list.append(round(juros, 2))
        amort_list.append(round(amort, 2))
        saldo -= amort

    # Inverte lógica: últimas amortizações são menores que as primeiras
    juros_list.reverse()
    amort_list.reverse()

    # Data inicial de vencimento (pode vir no JSON também)
    vencimento_base = datetime.strptime(data.get('data_base', '2025-05-12'), '%Y-%m-%d')

    cur = con.cursor()
    try:
        # Inserção de cada parcela com lógica invertida
        for mes in range(1, n + 1):
            juros_mes = juros_list[mes - 1]
            amortizacao = amort_list[mes - 1]

            data_vencimento = vencimento_base + relativedelta(months=mes - 1)
            data_pagamento = data_vencimento + timedelta(days=10)

            cur.execute(
                """
                INSERT INTO FINANCIAMENTOS (
                    ID_USUARIO,
                    ID_CARRO,
                    ID_MOTO,
                    NUMERO_DA_PARCELA,
                    VALOR_DA_PARCELA,
                    VALOR_DA_PARCELA_AMORTIZADA,
                    STATUS,
                    DATA_VENCIMENTO,
                    DATA_PAGAMENTO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id_usuario,
                    id_carro,
                    id_moto,
                    mes,
                    round(PMT, 2),
                    amortizacao,
                    'PENDENTE',
                    data_vencimento.date(),
                    data_pagamento.date()
                )
            )

        con.commit()
        return jsonify({'status': 'sucesso', 'mensagem': 'Parcelas geradas com sucesso.'}), 200

    except Exception as e:
        con.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400
