import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify
from main import app, con, senha_app_email
import random, re

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
