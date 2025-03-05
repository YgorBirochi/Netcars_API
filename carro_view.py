from flask import Flask, jsonify, request
from main import app, con
from datetime import datetime
import pytz

@app.route('/carro', methods=['GET'])
def get_carro():
    cursor = con.cursor()

    cursor.execute('''
    SELECT id_carro, marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria, 
    quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em FROM CARROS
    ''')

    fetch = cursor.fetchall()

    lista_carros = []

    for carro in list(fetch):
        lista_carros.append({
            'id_carro': carro[0],
            'marca': carro[1],
            'modelo': carro[2],
            'ano_modelo': carro[3],
            'ano_fabricacao': carro[4],
            'versao': carro[5],
            'cor': carro[6],
            'cambio': carro[7],
            'combustivel': carro[8],
            'categoria': carro[9],
            'quilometragem': carro[10],
            'estado': carro[11],
            'cidade': carro[12],
            'preco_compra': carro[13],
            'preco_venda': carro[14],
            'licenciado': carro[15],
            'placa': carro[16],
            'criado_em': carro[17]
        })

    qnt_carros = len(lista_carros)

    return jsonify({
        'success': f'{qnt_carros} carro(s) encontrado(s).',
        'veiculos': lista_carros
    })



@app.route('/carro', methods=['POST'])
def add_carro():
    data = request.get_json()

    # Lista de campos obrigatórios
    required_fields = [
        'marca', 'modelo', 'ano_modelo', 'ano_fabricacao', 'versao',
        'cor', 'cambio', 'combustivel', 'categoria', 'quilometragem',
        'estado', 'cidade', 'preco_compra', 'preco_venda', 'placa'
    ]

    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': 'Dados incompletos.',
            'missing_fields': missing_fields
        }), 400


    marca = data.get('marca')
    modelo = data.get('modelo')
    ano_modelo = data.get('ano_modelo')
    ano_fabricacao = data.get('ano_fabricacao')
    versao = data.get('versao')
    cor = data.get('cor')
    cambio = data.get('cambio')
    combustivel = data.get('combustivel')
    categoria = data.get('categoria')
    quilometragem = data.get('quilometragem')
    estado = data.get('estado')
    cidade = data.get('cidade')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    licenciado = data.get('licenciado')
    placa = data.get('placa')

    # Alterando fuso horário para o de Brasília
    criado_em = datetime.now(pytz.timezone('America/Sao_Paulo'))

    cursor = con.cursor()

    cursor.execute('''
    INSERT INTO CARROS
    (marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria, 
    quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em)
    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria,
    quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo cadastrado com sucesso!",
        'dados': {
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'versao': versao,
            'cor': cor,
            'cambio': cambio,
            'combustivel': combustivel,
            'categoria': categoria,
            'quilometragem': quilometragem,
            'estado': estado,
            'cidade': cidade,
            'preco_compra': preco_compra,
            'preco_venda': preco_venda,
            'licenciado': licenciado,
            'placa': placa,
            'criado_em': criado_em
        }
    })



