from flask import Flask
from flask_cors import CORS
import fdb

app = Flask(__name__)
CORS(app, origins=["*"])

app.config.from_pyfile('config.py')

host = app.config['DB_HOST']
database = app.config['DB_NAME']
user = app.config['DB_USER']
password = app.config['DB_PASSWORD']

senha_app_email = app.config['SENHA_APP_EMAIL']

senha_secreta = app.config['SECRET_KEY']
upload_folder = app.config['UPLOAD_FOLDER']

try:
    con = fdb.connect(host=host, database=database, user=user, password=password)
    print('Conexão estabelecida com sucesso')
except Exception as e:
    print(f'Error: {e}')

from login_cadastro_view import *
from carro_view import *
from moto_view import *
from relatorios_view import *
from esqueci_senha import *
from buscar_reserva import *
from gerar_pix import *
from manutencao import *
from financiamento import *
from venda import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)