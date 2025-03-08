from flask import Flask, jsonify, request
from main import app, con
from datetime import datetime
import pytz
import os, uuid

@app.route('/moto', methods=['GET'])
def get_moto():
    cursor = con.cursor()

    cursor.execute('''
    SELECT marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, marchas, partida, tipo_motor, 
        cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem, 
        preco_compra, preco_venda, placa, alimentacao, criado_em, ativo FROM MOTOS
    ''')

    fetch = cursor.fetchall()

    lista_motos = []

    for moto in fetch:
        lista_motos.append({
            'id_moto': moto[0],
            'marca': moto[1],
            'modelo': moto[2],
            'ano_modelo': moto[3],
            'ano_fabricacao': moto[4],
            'categoria': moto[5],
            'cor': moto[6],
            'marchas': moto[7],
            'partida': moto[8],
            'tipo_motor': moto[9],
            'cilindrada': moto[10],
            'freio_dianteiro_traseiro': moto[11],
            'refrigeracao': moto[12],
            'estado': moto[13],
            'cidade': moto[14],
            'quilometragem': moto[15],
            'preco_compra': moto[16],
            'preco_venda': moto[17],
            'placa': moto[18],
            'alimentacao': moto[19],
            'criado_em': moto[20],
            'ativo': moto[21]
        })

    qnt_motos = len(lista_motos)

    return jsonify({
        'success': f'{qnt_motos} moto(s) encontrada(s).',
        'veiculos': lista_motos
    }), 200


@app.route('/moto', methods=['POST'])
def add_moto():
    data = request.get_json()

    # Lista de campos obrigatórios
    required_fields = [
        'marca', 'modelo', 'ano_modelo', 'ano_fabricacao', 'categoria',
        'cor', 'marchas', 'partida', 'tipo_motor', 'cilindrada',
        'freio_dianteiro_traseiro', 'refrigeracao', 'estado', 'cidade',
        'quilometragem', 'preco_compra', 'preco_venda', 'placa', 'alimentacao'
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
    categoria = data.get('categoria')
    cor = data.get('cor')
    marchas = data.get('marchas')
    partida = data.get('partida')
    tipo_motor = data.get('tipo_motor')
    cilindrada = data.get('cilindrada')
    freio_dianteiro_traseiro = data.get('freio_dianteiro_traseiro')
    refrigeracao = data.get('refrigeracao')
    estado = data.get('estado')
    cidade = data.get('cidade')
    quilometragem = data.get('quilometragem')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    placa = data.get('placa')
    alimentacao = data.get('alimentacao')
    ativo = 1

    # Alterando fuso horário para o de Brasília
    criado_em = datetime.now(pytz.timezone('America/Sao_Paulo'))

    cursor = con.cursor()

    cursor.execute('''
    INSERT INTO MOTOS
    (marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, marchas, partida, tipo_motor, 
    cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem, 
    preco_compra, preco_venda, placa, criado_em, ativo, alimentacao)
    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, marchas, partida, tipo_motor,
    cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem,
    preco_compra, preco_venda, placa, criado_em, ativo, alimentacao))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo cadastrado com sucesso!",
        'dados': {
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'categoria': categoria,
            'cor': cor,
            'marchas': marchas,
            'partida': partida,
            'tipo_motor': tipo_motor,
            'cilindrada': cilindrada,
            'freio_dianteiro_traseiro': freio_dianteiro_traseiro,
            'refrigeracao': refrigeracao,
            'estado': estado,
            'cidade': cidade,
            'quilometragem': quilometragem,
            'preco_compra': preco_compra,
            'preco_venda': preco_venda,
            'placa': placa,
            'alimentacao': alimentacao,
            'criado_em': criado_em,
            'ativo': ativo
        }
    }), 200

@app.route('/moto/<int:id>', methods=['DELETE'])
def deletar_moto(id):
    cursor = con.cursor()

    cursor.execute('SELECT 1 FROM motos WHERE ID_MOTO = ?', (id,))

    if not cursor.fetchone():
        return jsonify({'error': 'Veículo não encontrado.'}), 404

    cursor.execute('DELETE FROM MOTOS WHERE ID_MOTO = ?', (id,))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo deletado com sucesso!"
    })

@app.route('/moto/<int:id>', methods=['PUT'])
def editar_moto(id):
    cursor = con.cursor()

    # Verificando a existência do carro
    cursor.execute('SELECT 1 FROM MOTOS WHERE ID_MOTO = ?', (id,))
    if not cursor.fetchone():
        return jsonify({'error': 'Veículo não encontrado.'}), 404

    data = request.get_json()

    fields = [
        'marca', 'modelo', 'ano_modelo', 'ano_fabricacao', 'categoria',
        'cor', 'marchas', 'partida', 'tipo_motor', 'cilindrada',
        'freio_dianteiro_traseiro', 'refrigeracao', 'estado', 'cidade',
        'quilometragem', 'preco_compra', 'preco_venda', 'placa', 'alimentacao',
        'ativo'
    ]

    cursor.execute('''
        SELECT marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, marchas, partida, tipo_motor, 
        cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem, 
        preco_compra, preco_venda, placa, criado_em, ativo, alimentacao
        FROM MOTOS WHERE ID_MOTO = ?
    ''', (id,))

    data_ant = []
    for item in cursor.fetchone():
        data_ant.append(item)

    for i in range(len(data_ant)):
        print(fields[i])
        if data.get(fields[i]) == data_ant[i] or not data.get(fields[i]):
            data[fields[i]] = data_ant[i]

    marca = data.get('marca')
    modelo = data.get('modelo')
    ano_modelo = data.get('ano_modelo')
    ano_fabricacao = data.get('ano_fabricacao')
    categoria = data.get('categoria')
    cor = data.get('cor')
    marchas = data.get('marchas')
    partida = data.get('partida')
    tipo_motor = data.get('tipo_motor')
    cilindrada = data.get('cilindrada')
    freio_dianteiro_traseiro = data.get('freio_dianteiro_traseiro')
    refrigeracao = data.get('refrigeracao')
    estado = data.get('estado')
    cidade = data.get('cidade')
    quilometragem = data.get('quilometragem')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    placa = data.get('placa')
    alimentacao = data.get('alimentacao')
    ativo = data.get('ativo')
    criado_em = data.get('criado_em')

    cursor.execute('''
        UPDATE MOTOS
        SET marca =?, modelo =?, ano_modelo =?, ano_fabricacao =?, categoria =?, cor =?, marchas =?, partida =?, tipo_motor =?, 
        cilindrada=?, freio_dianteiro_traseiro =?, refrigeracao, =?, estado =?, cidade =?,  quilometragem =?, preco_compra =?, 
        preco_venda =?, placa =?, criado_em = ?, ativo =?, alimentacao = ?
        where ID_MOTO = ?
        ''',
       (marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, marchas, partida, tipo_motor,
        cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem,
        preco_compra, preco_venda, placa, criado_em, ativo, alimentacao))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo editado com sucesso!",
        'dados': {
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'categoria': categoria,
            'cor': cor,
            'marchas': marchas,
            'partida': partida,
            'tipo_motor': tipo_motor,
            'cilindrada': cilindrada,
            'freio_dianteiro_traseiro': freio_dianteiro_traseiro,
            'refrigeracao': refrigeracao,
            'estado': estado,
            'cidade': cidade,
            'quilometragem': quilometragem,
            'preco_compra': preco_compra,
            'preco_venda': preco_venda,
            'placa': placa,
            'alimentacao': alimentacao,
            'criado_em': criado_em,
            'ativo': ativo
        }
    }), 200


