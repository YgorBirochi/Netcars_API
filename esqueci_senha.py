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
                @import url('https://fonts.googleapis.com/css2?family=Racing+Sans+One&family=Poppins:wght@300;400;500;600;700&display=swap');
        
                body {{
                    font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
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
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
                }}
        
                .header {{
                    background: linear-gradient(135deg, #7928CA, #6C1DE9);
                    padding: 35px 20px;
                    text-align: center;
                    color: #fff;
                    position: relative;
                    overflow: hidden;
                }}
        
                .header::before {{
                    content: "";
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    z-index: 0;
                }}
        
                .logo-container {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 20px;
                    position: relative;
                    z-index: 1;
                }}
        
                .logo-icon {{
                    width: auto;
                    height: 40px;
                    vertical-align: middle;
                    animation: pulse 2s infinite ease-in-out;
                }}
        
                @keyframes pulse {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.05); }}
                    100% {{ transform: scale(1); }}
                }}
        
                .header h1 {{
                    margin: 0;
                    font-size: 38px;
                    letter-spacing: 2px;
                    font-family: "Racing Sans One", serif;
                }}
        
                .header-subtitle {{
                    color: rgba(255, 255, 255, 0.95);
                    margin-top: 10px;
                    font-size: 16px;
                    font-weight: 300;
                    letter-spacing: 0.5px;
                }}
        
                .content {{
                    padding: 40px 45px;
                    position: relative;
                    z-index: 1;
                }}
        
                .content::before {{
                    content: "";
                    position: absolute;
                    top: 0;
                    right: 0;
                    width: 150px;
                    height: 150px;
                    background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M60.8 20.8l-4.2 4.2 12.8 12.8H0v6h69.4L56.6 56.6l4.2 4.2L79.2 42 60.8 20.8z' fill='%236C1DE9' fill-opacity='0.05'/%3E%3C/svg%3E");
                    background-repeat: no-repeat;
                    background-size: cover;
                    opacity: 0.4;
                    z-index: -1;
                }}
        
                .content p {{
                    line-height: 1.8;
                    margin-bottom: 24px;
                    font-size: 15px;
                    color: #444;
                }}
        
                .greeting {{
                    font-size: 22px;
                    color: #222;
                    margin-bottom: 25px;
                    font-weight: 600;
                    position: relative;
                    display: inline-block;
                }}
        
                .greeting::after {{
                    content: "";
                    display: block;
                    width: 40px;
                    height: 3px;
                    background: linear-gradient(90deg, #6C1DE9, #9F6EFF);
                    margin-top: 8px;
                    border-radius: 2px;
                }}
        
                .verification-box {{
                    background: linear-gradient(145deg, #f7f5fe, #ffffff);
                    border-left: 4px solid #6C1DE9;
                    padding: 25px;
                    margin: 35px 0;
                    text-align: center;
                    border-radius: 8px;
                    box-shadow: 0 6px 16px rgba(108, 29, 233, 0.08), 0 3px 6px rgba(0, 0, 0, 0.04);
                    position: relative;
                    overflow: hidden;
                }}
        
                .verification-box::before {{
                    content: "";
                    position: absolute;
                    top: -50px;
                    left: -50px;
                    width: 100px;
                    height: 100px;
                    background-color: rgba(108, 29, 233, 0.05);
                    border-radius: 50%;
                }}
        
                .verification-box::after {{
                    content: "";
                    position: absolute;
                    bottom: -60px;
                    right: -60px;
                    width: 120px;
                    height: 120px;
                    background-color: rgba(108, 29, 233, 0.05);
                    border-radius: 50%;
                }}
        
                .verification-title {{
                    color: #6C1DE9;
                    font-size: 16px;
                    font-weight: 600;
                    margin-bottom: 16px;
                    position: relative;
                    display: inline-block;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
        
                .verification-title::before,
                .verification-title::after {{
                    content: "✦";
                    display: inline-block;
                    color: #6C1DE9;
                    opacity: 0.5;
                    margin: 0 10px;
                    font-size: 14px;
                }}
        
                .codigo {{
                    display: inline-block;
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #6C1DE9;
                    padding: 15px 25px;
                    background-color: #fff;
                    border-radius: 10px;
                    border: 1px solid #e2d7f7;
                    box-shadow: 0 3px 10px rgba(108, 29, 233, 0.12);
                    position: relative;
                    z-index: 1;
                    transition: all 0.3s ease;
                }}
        
                .codigo:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(108, 29, 233, 0.18);
                }}
        
                .help-section {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin-top: 35px;
                    position: relative;
                }}
        
        
                .help-section p {{
                    font-size: 14px;
                    color: #666;
                    text-align: center;
                    max-width: 90%;
                }}
        
                .contact-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #7928CA, #6C1DE9);
                    color: #fff;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 50px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    margin-top: 15px;
                    box-shadow: 0 4px 10px rgba(108, 29, 233, 0.25);
                    position: relative;
                    overflow: hidden;
                }}
        
                .contact-button::before {{
                    content: "";
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                    transition: all 0.6s ease;
                }}
        
                .contact-button:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 6px 12px rgba(108, 29, 233, 0.3);
                }}
        
                .contact-button:hover::before {{
                    left: 100%;
                }}
        
                .footer {{
                    background: linear-gradient(to right, #f7f5fe, #f0ebfd);
                    text-align: center;
                    padding: 25px 20px;
                    font-size: 13px;
                    color: #777;
                    border-top: 1px solid #e8e0f9;
                    position: relative;
                }}
        
                .social-links {{
                    margin-bottom: 18px;
                }}
        
                .social-icon {{
                    display: inline-block;
                    width: 34px;
                    height: 34px;
                    line-height: 34px;
                    text-align: center;
                    background: linear-gradient(135deg, #7928CA, #6C1DE9);
                    color: white;
                    border-radius: 50%;
                    margin: 0 6px;
                    font-size: 14px;
                    text-decoration: none;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 6px rgba(108, 29, 233, 0.2);
                }}
        
                .social-icon:hover {{
                    transform: translateY(-3px) scale(1.1);
                    box-shadow: 0 5px 10px rgba(108, 29, 233, 0.3);
                }}
        
                .footer-links {{
                    margin-top: 15px;
                }}
        
                .footer-links a {{
                    color: #6C1DE9;
                    text-decoration: none;
                    margin: 0 12px;
                    position: relative;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }}
        
                .footer-links a::after {{
                    content: "";
                    position: absolute;
                    width: 0;
                    height: 1px;
                    bottom: -2px;
                    left: 0;
                    background-color: #6C1DE9;
                    transition: all 0.3s ease;
                }}
        
                .footer-links a:hover::after {{
                    width: 100%;
                }}
        
                .notice {{
                    font-size: 12px;
                    color: #999;
                    margin-top: 18px;
                    font-style: italic;
                }}
        
                .security-badge {{
                    display: inline-block;
                    font-size: 12px;
                    background-color: #edf7ed;
                    color: #43a047;
                    padding: 5px 12px;
                    border-radius: 30px;
                    margin-top: 12px;
                    border: 1px solid rgba(67, 160, 71, 0.2);
                }}
        
                .security-badge::before {{
                    content: "✓";
                    margin-right: 5px;
                    font-weight: bold;
                }}
        
                .time-badge {{
                    display: inline-block;
                    background-color: #ffebee;
                    color: #e53935;
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: 500;
                    margin-left: 5px;
                    position: relative;
                    top: -1px;
                }}
        
                .time-badge::before {{
                    content: "⏱";
                    margin-right: 4px;
                    font-size: 12px;
                }}
            </style>
        </head>
        
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo-container">
                        <img class="logo-icon" src="../upload/imagensApi/logo.png" alt="Logo">
                        <h1><span style="color: #000;">NET</span>CARS</h1>
                    </div>
                </div>
                <div class="content">
                    <p class="greeting">Olá, prezado(a) cliente!</p>
                    
                    <p>Recebemos uma solicitação para recuperação de senha da sua conta <strong>NetCars</strong>. Para garantir a segurança dos seus dados e completar este processo, utilize o código de verificação abaixo:</p>
                    
                    <div class="verification-box">
                        <div class="verification-title">SEU CÓDIGO DE VERIFICAÇÃO</div>
                        <div class="codigo">{codigo}</div>
                        <div style="margin-top: 15px; font-size: 13px; color: #777;">
                            Válido por <span class="time-badge">10 minutos</span>
                        </div>
                    </div>
                    
                    <p>Este código é válido por <strong>10 minutos</strong>. Por favor, não compartilhe este código com ninguém, incluindo a equipe da NetCars, pois nossos colaboradores nunca solicitarão esta informação.</p>
                    
                    <p>Se você não solicitou a alteração de senha, recomendamos que entre em contato com nossa equipe de suporte imediatamente para proteger sua conta.</p>
                    
                    <div class="help-section">
                        <div class="security-badge">Email verificado e seguro</div>
                    </div>
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
