from flask import Flask, request, jsonify, url_for, send_from_directory
from main import app, con, upload_folder
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

@app.route('/uploads/logo')
def get_logo_img():
    return send_from_directory(
        os.path.join(app.root_path, 'upload', 'Logo'),
        'logo.png'
    )

@app.route('/obter_logo', methods=["GET"])
def obter_logo():
    imagem_url = url_for('get_logo_img', _external=True)
    # normalmente retornamos 200, mas se quiser 400, mantenha
    return jsonify({'img_url': imagem_url}), 200

# Caminho onde o logo será salvo
UPLOAD_FOLDER = os.path.join(app.root_path, 'upload', 'Logo')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Função auxiliar para validar extensões
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/editar_logo', methods=['POST'])
def editar_logo():
    if 'file' not in request.files:
        return jsonify({'error': 'Arquivo não enviado'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    if file and allowed_file(file.filename):
        # Garante que a pasta exista
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Caminho completo onde o arquivo será salvo como logo.png
        logo_path = os.path.join(UPLOAD_FOLDER, 'logo.png')

        # Salva o arquivo substituindo o antigo
        file.save(logo_path)

        return jsonify({'success': 'Logo atualizado com sucesso!'}), 200
    else:
        return jsonify({'error': 'Extensão de arquivo não permitida'}), 400
