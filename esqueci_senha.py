import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, request, jsonify, url_for, send_from_directory
from main import app, con, senha_app_email, upload_folder
import random, re
from flask_bcrypt import generate_password_hash, check_password_hash
import os

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

        # Usar SSL direto (porta 465) em vez de TLS (porta 587)
        porta_smtp = 465

        assunto = 'NetCars - Código de Verificação'
        corpo = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>NetCars - Código de Verificação</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    line-height: 1.6;
                }}
        
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #fff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                }}
        
                .header {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                    background-color: #6C1DE9;
                    padding: 30px 20px;
                    color: #fff;
                }}
        
                .header h1 {{
                    width: 100%;
                    text-align: center;
                    font-size: 30px;
                    font-style: italic;
                }}
        
                .header-subtitle {{
                    color: rgba(255, 255, 255, 0.9);
                    margin-top: 5px;
                    font-size: 16px;
                }}
        
                .content {{
                    padding: 35px 40px;
                }}
        
                .content p {{
                    line-height: 1.7;
                    margin-bottom: 22px;
                    font-size: 15px;
                    color: #444;
                }}
        
                .greeting {{
                    font-size: 20px;
                    color: #222;
                    margin-bottom: 25px;
                    font-weight: 500;
                }}
        
                .verification-box {{
                    background-color: #f7f5fe;
                    border-left: 4px solid #6C1DE9;
                    padding: 20px;
                    margin: 30px 0;
                    text-align: center;
                    border-radius: 4px;
                }}
        
                .verification-title {{
                    color: #6C1DE9;
                    font-size: 16px;
                    font-weight: 600;
                    margin-bottom: 12px;
                }}
        
                .codigo {{
                    display: inline-block;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 5px;
                    color: #6C1DE9;
                    padding: 12px 20px;
                    background-color: #fff;
                    border-radius: 6px;
                    border: 1px solid #e2d7f7;
                    box-shadow: 0 2px 6px rgba(108, 29, 233, 0.1);
                }}
        
                .help-section {{
                    display: flex;
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 25px;
                    border-top: 1px solid #eee;
                }}
        
                .help-section p {{
                    font-size: 14px;
                    color: #666;
                }}
        
                .contact-button {{
                    display: inline-block;
                    background-color: #6C1DE9;
                    color: #fff;
                    padding: 12px 25px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    margin-top: 5px;
                }}
        
                .contact-button:hover {{
                    background-color: #5a18c0;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(108, 29, 233, 0.2);
                }}
        
                .footer {{
                    background-color: #f7f5fe;
                    text-align: center;
                    padding: 20px;
                    font-size: 13px;
                    color: #777;
                    border-top: 1px solid #e8e0f9;
                }}
        
                .social-links {{
                    margin-bottom: 15px;
                }}
        
                .social-icon {{
                    display: inline-block;
                    width: 30px;
                    height: 30px;
                    line-height: 30px;
                    text-align: center;
                    background-color: #6C1DE9;
                    color: white;
                    border-radius: 50%;
                    margin: 0 5px;
                    font-size: 14px;
                    text-decoration: none;
                }}
        
                .footer-links {{
                    margin-top: 10px;
                }}
        
                .footer-links a {{
                    color: #6C1DE9;
                    text-decoration: none;
                    margin: 0 10px;
                }}
        
                .footer-links a:hover {{
                    text-decoration: underline;
                }}
        
                .notice {{
                    font-size: 12px;
                    color: #999;
                    margin-top: 15px;
                }}
            </style>
        </head>
        
        <body>
            <div class="container">
                <div class="header">
                    <h1><span style="color: black;">NET</span>CARS</h1>
                </div>
                <div class="content">
                    <p class="greeting">Olá, prezado(a) cliente!</p>
                    
                    <p>Recebemos uma solicitação para recuperação de senha da sua conta <strong>NetCars</strong>. Para garantir a segurança dos seus dados e completar este processo, utilize o código de verificação abaixo:</p>
                    
                    <div class="verification-box">
                        <div class="verification-title">SEU CÓDIGO DE VERIFICAÇÃO</div>
                        <div class="codigo">{codigo}</div>
                    </div>
                    
                    <p>Este código é válido por <strong>10 minutos</strong>. Por favor, não compartilhe este código com ninguém, incluindo a equipe da NetCars, pois nossos colaboradores nunca solicitarão esta informação.</p>
                    
                    <p>Se você não solicitou a alteração de senha, recomendamos que entre em contato com nossa equipe de suporte imediatamente para proteger sua conta.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} NetCars. Todos os direitos reservados.</p>
                    <div class="footer-links">
                        <a href="#">Termos de Uso</a>
                        <a href="#">Política de Privacidade</a>
                        <a href="#">Ajuda</a>
                    </div>
                    <p class="notice">Este é um e-mail automático, por favor não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = email_destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'html'))

        try:
            # Usando SSL direto (mais confiável com Gmail)
            server = smtplib.SMTP_SSL(servidor_smtp, porta_smtp, timeout=30)
            server.set_debuglevel(1)  # Ative para debugging
            server.ehlo()  # Identifica-se ao servidor
            server.login(remetente, senha)
            text = msg.as_string()
            server.sendmail(remetente, email_destinatario, text)
            server.quit()
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

@app.route('/validar_codigo', methods=['POST'])
def validar_codigo():
    data = request.get_json()
    email = data.get('email')
    codigo = str(data.get('codigo'))

    if not email or not codigo:
        return jsonify({'error': 'Dados incompletos.'}), 400

    cursor = con.cursor()

    cursor.execute("SELECT id_usuario, codigo_criado_em, codigo FROM USUARIO WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user is None:
        return jsonify({'error': 'Email não cadastrado.'}), 404

    user_id = user[0]
    codigo_criado_em = user[1]
    codigo_valido = str(user[2])

    horario_atual = datetime.now()

    if horario_atual - codigo_criado_em > timedelta(minutes=10):
        return jsonify({'error': 'Código expirado.'}), 401

    if codigo != codigo_valido:
        return jsonify({'error': 'Código incorreto. Verifique novamente seu email.'}), 401

    cursor.execute('UPDATE USUARIO SET codigo = NULL, codigo_criado_em = NULL, trocar_senha = true WHERE id_usuario = ?', (user_id,))
    con.commit()
    cursor.close()

    return jsonify({'success': 'Código válido.'}), 200

@app.route('/redefinir_senha', methods=['POST'])
def redefinir_senha():
    data = request.get_json()
    senha_nova = data.get('senha_nova')
    repetir_senha_nova = data.get('repetir_senha_nova')
    email = data.get('email')

    if not senha_nova:
        return jsonify({'error': 'Senha nova não pode estar vazia.'}), 400

    if not repetir_senha_nova:
        return jsonify({'error': 'Repetir a senha nova não pode estar vazia.'}), 400

    if not email:
        return jsonify({'error': 'Email não pode estar vazio.'}), 400

    if not senha_nova or not repetir_senha_nova or not email:
        return jsonify({'error': 'Dados incompletos.'}), 400

    if senha_nova != repetir_senha_nova:
        return jsonify({'error': 'As senhas são diferentes.'}), 400

    verificar_validar_senha = validar_senha(senha_nova)
    if verificar_validar_senha != True:
        return jsonify({'error': verificar_validar_senha}), 400

    cursor = con.cursor()

    cursor.execute('SELECT TROCAR_SENHA FROM USUARIO WHERE EMAIL = ?', (email,))
    user = cursor.fetchone()
    if user is None:
        return jsonify({'error': 'Email não cadastrado.'}), 404

    trocar_senha = user[0]

    if trocar_senha is not True:
        return jsonify({'error': 'Não foi possível redefinir a senha.'}), 401

    cursor.execute('SELECT SENHA_HASH FROM USUARIO WHERE EMAIL = ?', (email,))
    senha_antiga = cursor.fetchone()[0]

    if check_password_hash(senha_antiga, senha_nova):
        return jsonify({'error': 'A senha nova não pode ser igual à anterior.'}), 400

    senha_hash = generate_password_hash(senha_nova)
    cursor.execute('UPDATE USUARIO SET SENHA_HASH = ?, TROCAR_SENHA = NULL WHERE EMAIL = ?', (senha_hash, email))

    con.commit()
    cursor.close()

    return jsonify({'success': 'Senha redefinida com sucesso.'}), 200
