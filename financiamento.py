from flask import Flask, request, jsonify
from main import app, con
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


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
