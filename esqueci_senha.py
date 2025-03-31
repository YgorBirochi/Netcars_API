import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, request, jsonify
from main import app, con, senha_app_email, senha_secreta
import jwt
import random, re
from flask_bcrypt import generate_password_hash, check_password_hash

# -----------------------------
# Funções Auxiliares (Banco e Senha)
# -----------------------------
def validar_senha(senha):
    if len(senha) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
        return "A senha deve conter pelo menos um símbolo especial (!@#$%^&*...)."
    if not re.search(r"[A-Z]", senha):
        return "A senha deve conter pelo menos uma letra maiúscula."
    return True

def buscar_dados_carro_por_id(id_carro):
    cursor = con.cursor()
    query = '''
        SELECT id_carro, marca, modelo, ano_modelo, ano_fabricacao, versao, cor, renavam,
               cambio, combustivel, categoria, quilometragem, estado, cidade, preco_compra,
               preco_venda, licenciado, placa, criado_em, ativo 
        FROM CARROS
        WHERE id_carro = ?
    '''
    cursor.execute(query, (id_carro,))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado:
        return {
            'id': resultado[0],
            'marca': resultado[1],
            'modelo': resultado[2],
            'ano_modelo': resultado[3],
            'ano_fabricacao': resultado[4],
            'versao': resultado[5],
            'cor': resultado[6],
            'renavam': resultado[7],
            'cambio': resultado[8],
            'combustivel': resultado[9],
            'categoria': resultado[10],
            'quilometragem': resultado[11],
            'estado': resultado[12],
            'cidade': resultado[13],
            'preco_compra': resultado[14],
            'preco_venda': resultado[15],
            'licenciado': resultado[16],
            'placa': resultado[17],
            'criado_em': resultado[18],
            'ativo': resultado[19],
        }
    return None

def buscar_dados_moto_por_id(id_moto):
    cursor = con.cursor()
    query = '''
        SELECT id_moto, marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, 
               marchas, partida, tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao,
               estado, cidade, quilometragem, preco_compra, preco_venda, placa, alimentacao, criado_em, ativo
        FROM MOTOS
        WHERE id_moto = ?
    '''
    cursor.execute(query, (id_moto,))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado:
        return {
            'id_moto': resultado[0],
            'marca': resultado[1],
            'modelo': resultado[2],
            'ano_modelo': resultado[3],
            'ano_fabricacao': resultado[4],
            'categoria': resultado[5],
            'cor': resultado[6],
            'renavam': resultado[7],
            'marchas': resultado[8],
            'partida': resultado[9],
            'tipo_motor': resultado[10],
            'cilindrada': resultado[11],
            'freio_dianteiro_traseiro': resultado[12],
            'refrigeracao': resultado[13],
            'estado': resultado[14],
            'cidade': resultado[15],
            'quilometragem': resultado[16],
            'preco_compra': resultado[17],
            'preco_venda': resultado[18],
            'placa': resultado[19],
            'alimentacao': resultado[20],
            'criado_em': resultado[21],
            'ativo': resultado[22]
        }
    return None

# -----------------------------
# Envio de E-mail de Reserva (Assíncrono)
# -----------------------------
def enviar_email_reserva(email_destinatario, tipo_veiculo, dados_veiculo):
    def task_envio():
        remetente = 'netcars.contato@gmail.com'
        senha = senha_app_email
        servidor_smtp = 'smtp.gmail.com'
        porta_smtp = 587

        # Calcular data limite para comparecimento (3 dias a partir de hoje)
        data_envio = datetime.now()
        data_limite = data_envio + timedelta(days=3)
        data_limite_str = data_limite.strftime("%d/%m/%Y")

        # Endereço fictício da concessionária
        endereco_concessionaria = "Av. Exemplo, 1234 - Centro, Cidade Fictícia"

        # Montar o corpo do e-mail
        assunto = "NetCars - Confirmação de Reserva"
        corpo_email = f"""Prezado(a) Cliente,

Sua reserva de {tipo_veiculo} foi confirmada com sucesso!

Dados do veículo:
- Marca: {dados_veiculo['marca']}
- Modelo: {dados_veiculo['modelo']}
- Preço de Venda: R$ {dados_veiculo['preco_venda']:.2f}
- Ano Modelo: {dados_veiculo['ano_modelo']}
- Ano Fabricação: {dados_veiculo['ano_fabricacao']}
- Cor: {dados_veiculo['cor']}

Você tem até o dia {data_limite_str} para comparecer à nossa concessionária para finalizar sua compra:

Endereço: {endereco_concessionaria}

Aguardamos a sua visita!

Atenciosamente,
Equipe NetCars
"""
        # Configurando o cabeçalho do e-mail
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = email_destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo_email, 'plain'))

        try:
            server = smtplib.SMTP(servidor_smtp, porta_smtp, timeout=10)
            # Opcional: Ative o debug se necessário: server.set_debuglevel(1)
            server.starttls()
            server.login(remetente, senha)
            text = msg.as_string()
            server.sendmail(remetente, email_destinatario, text)
            server.quit()
            print(f"E-mail de reserva enviado para {email_destinatario}")
        except Exception as e:
            print(f"Erro ao enviar e-mail de reserva: {e}")

    # Inicia a thread para envio assíncrono
    Thread(target=task_envio, daemon=True).start()

# -----------------------------
# Envio de E-mail de Recuperação de Senha (Assíncrono)
# -----------------------------
def enviar_email_recuperar_senha(email_destinatario, codigo):
    def task_envio():
        remetente = 'netcars.contato@gmail.com'
        senha = senha_app_email
        servidor_smtp = 'smtp.gmail.com'
        porta_smtp = 587

        assunto = 'NetCars - Código de Verificação'
        corpo = f'O seu código de verificação é: {codigo}'

        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = email_destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))

        try:
            server = smtplib.SMTP(servidor_smtp, porta_smtp, timeout=10)
            # Opcional: server.set_debuglevel(1)
            server.starttls()
            server.login(remetente, senha)
            text = msg.as_string()
            server.sendmail(remetente, email_destinatario, text)
            server.quit()
            print(f"E-mail de recuperação enviado para {email_destinatario}")
        except Exception as e:
            print(f"Erro ao enviar e-mail de recuperação: {e}")

    Thread(target=task_envio, daemon=True).start()

# -----------------------------
# Rotas
# -----------------------------

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

@app.route('/reservar_veiculo', methods=["POST"])
def reservar_veiculo():
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
    id_veiculo = data.get('id_veiculo')
    tipo_veiculo = data.get('tipo_veiculo')

    if not id_veiculo or not id_usuario or not tipo_veiculo:
        return jsonify({"error": "Informações incompletas."}), 400

    cursor = con.cursor()
    cursor.execute('SELECT EMAIL, TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    dados_user = cursor.fetchone()
    if not dados_user:
        return jsonify({'error': 'Cliente não encontrado.'}), 400

    if dados_user[1] != 3:
        return jsonify({'error': 'Apenas clientes podem fazer reservas.'}), 400

    email = dados_user[0]
    if tipo_veiculo == "carro":
        dados_veiculo = buscar_dados_carro_por_id(id_veiculo)
    elif tipo_veiculo == "moto":
        dados_veiculo = buscar_dados_moto_por_id(id_veiculo)
    else:
        return jsonify({'error': 'Tipo de veículo inválido.'}), 400

    if not dados_veiculo:
        return jsonify({'error': 'Veículo não encontrado.'}), 400

    # Verifica se o veículo já está reservado
    cursor.execute(f'SELECT RESERVADO FROM {tipo_veiculo}s WHERE ID_{tipo_veiculo} = ?', (id_veiculo,))
    row = cursor.fetchone()
    if row and row[0] is True:
        return jsonify({'error': 'Veículo já reservado.'}), 400

    # Atualiza a reserva no banco
    data_envio = datetime.now()
    cursor.execute(
        f'UPDATE {tipo_veiculo}s SET RESERVADO = true, RESERVADO_EM = ?, ID_USUARIO_RESERVA = ? WHERE ID_{tipo_veiculo} = ?',
        (data_envio, id_usuario, id_veiculo)
    )
    con.commit()
    cursor.close()

    # Envia o e-mail de reserva de forma assíncrona
    enviar_email_reserva(email, tipo_veiculo, dados_veiculo)

    return jsonify({'success': f"Um email com mais informações foi enviado para {email}"}), 200

@app.route('/gerar_codigo', methods=['POST'])
def gerar_codigo():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Usuário não encontrado.'}), 400

    cursor = con.cursor()
    cursor.execute("SELECT id_usuario FROM USUARIO WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user is None:
        return jsonify({'error': 'Email não cadastrado.'}), 404
    user_id = user[0]

    codigo = ''.join(random.choices('0123456789', k=6))
    codigo_criado_em = datetime.now()

    # Envia o e-mail de recuperação de senha de forma assíncrona
    enviar_email_recuperar_senha(email, codigo)

    cursor.execute("UPDATE USUARIO SET codigo = ?, codigo_criado_em = ? WHERE id_usuario = ?", (codigo, codigo_criado_em, user_id))
    con.commit()
    cursor.close()

    return jsonify({'success': 'Código enviado para o e-mail.'}), 200

@app.route('/buscar_reservas', methods=['GET'])
def buscar_reserva():
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

    cursor.execute("SELECT ID_CARRO FROM CARROS WHERE RESERVADO = True AND ID_USUARIO_RESERVA = ?", (id_usuario,))

    data = cursor.fetchall()

    if not data:
        return []

    id_carro = [row[0] for row in data]

    dadosVeic = [buscar_dados_carro_por_id(id) for id in id_carro]

    return dadosVeic