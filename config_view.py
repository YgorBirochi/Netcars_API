from flask import Flask, request, jsonify
from main import app, con
import os

@app.route('/obter_nome_garagem', methods=["GET"])
def obter_nome_garagem():
    cursor = con.cursor()

    cursor.execute('SELECT PRIMEIRO_NOME, SEGUNDO_NOME FROM CONFIG_GARAGEM WHERE ID_CONFIG_GARAGEM = 1')

    data = cursor.fetchone()

    primeiro_nome = data[0]
    segundo_nome = data[1]

    return jsonify({
        'primeiro_nome': primeiro_nome,
        'segundo_nome': segundo_nome
    }), 200


@app.route('/obter_config_garagem', methods=["GET"])
def obter_config_garagem():
    cursor = con.cursor()

    cursor.execute('''
        SELECT PRIMEIRO_NOME, 
        SEGUNDO_NOME,
        RAZAO_SOCIAL,
        CHAVE_PIX,
        CNPJ, 
        CIDADE,
        ESTADO 
        FROM CONFIG_GARAGEM 
        WHERE ID_CONFIG_GARAGEM = 1
    ''')

    data = cursor.fetchone()

    primeiro_nome = data[0] if len(data) > 0 else ""
    segundo_nome = data[1] if len(data) > 1 else ""
    razao_social = data[2] if len(data) > 2 else ""
    chave_pix = data[3] if len(data) > 3 else ""
    cnpj = data[4] if len(data) > 4 else ""
    cidade = data[5] if len(data) > 5 else ""
    estado = data[6] if len(data) > 6 else ""

    cursor.close()

    return jsonify({
        'primeiro_nome': primeiro_nome,
        'segundo_nome': segundo_nome,
        'razao_social': razao_social,
        'chave_pix': chave_pix,
        'cnpj': cnpj,
        'cidade': cidade,
        'estado': estado
    }), 200

@app.route('/att_config_garagem', methods=["PUT"])
def att_config_garagem():
    data = request.get_json() or {}

    primeiro_nome = data.get('primeiro_nome', "")
    segundo_nome = data.get('segundo_nome', "")
    razao_social = data.get('razao_social', "")
    chave_pix = data.get('chave_pix', "")
    cnpj = data.get('cnpj', "")
    cidade = data.get('cidade', "")
    estado = data.get('estado', "")

    if not primeiro_nome or not segundo_nome or not razao_social or not chave_pix or not cnpj or not cidade or not estado:
        return jsonify({'error': 'Dados incompletos'}), 400

    cursor = con.cursor()
    cursor.execute("""
        UPDATE CONFIG_GARAGEM
        SET
            PRIMEIRO_NOME = ?,
            SEGUNDO_NOME = ?,
            RAZAO_SOCIAL = ?,
            CHAVE_PIX = ?,
            CNPJ = ?,
            CIDADE = ?,
            ESTADO = ?
        WHERE ID_CONFIG_GARAGEM = 1
    """, (
        primeiro_nome,
        segundo_nome,
        razao_social,
        chave_pix,
        cnpj,
        cidade,
        estado
    ))

    con.commit()
    cursor.close()

    return jsonify({'success': 'Dados atualizados com sucesso!'}), 200

@app.route('/obter_logo', methods=["GET"])
def obter_logo():
    # Define o caminho para a pasta de imagens do carro (ex: uploads/Carros/<id_carro>)
    images_dir = os.path.join(app.root_path, upload_folder, 'Carros', str(id_carro))
    imagens = []

    # Verifica se o diretório existe
    if os.path.exists(images_dir):
        for file in os.listdir(images_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                imagem_url = url_for('get_car_image', id_carro=id_carro, filename=file, _external=True)
                imagens.append(imagem_url)
