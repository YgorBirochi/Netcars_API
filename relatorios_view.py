from flask import Flask, send_file
from main import app, con
from fpdf import FPDF

def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_kilometragem(value):
    return f"{value:,} km".replace(",", ".")

class CustomPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Relação de Veículos", ln=True, align='C')
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


@app.route('/relatorio/carros', methods=['GET'])
def criar_pdf_carro():
    cursor = con.cursor()
    cursor.execute("SELECT marca, modelo, placa, ano_modelo, ano_fabricacao, cor, renavam, cambio, combustivel, categoria, quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, versao FROM carros")
    carros = cursor.fetchall()
    cursor.close()

    total_veiculos = len(carros)

    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    carros_por_pagina = 3
    contador = 0

    for carro in carros:
        if contador == carros_por_pagina:
            pdf.add_page()
            contador = 0

        campos = [
            ("Marca", carro[0]), ("Modelo", carro[1]), ("Placa", carro[2]),
            ("Ano Modelo", carro[3]), ("Ano Fabricação", carro[4]), ("Cor", carro[5]),
            ("Renavam", carro[6]), ("Câmbio", carro[7]), ("Combustível", carro[8]),
            ("Categoria", carro[9]), ("Quilometragem", format_kilometragem(carro[10])),
            ("Estado", carro[11]), ("Cidade", carro[12]), ("Preço Compra", format_currency(carro[13])),
            ("Preço Venda", format_currency(carro[14])), ("Licenciado", "Sim" if carro[15] == 1 else "Não"),
            ("Versão", carro[16])
        ]

        for i in range(0, len(campos) - 1, 2):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(35, 10, f"{campos[i][0]}:", border=0)
            pdf.set_font("Arial", "", 12)
            pdf.cell(40, 10, str(campos[i][1]), border=0)

            if i + 1 < len(campos) - 1:
                pdf.set_x(120)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(35, 10, f"{campos[i + 1][0]}:", border=0)
                pdf.set_font("Arial", "", 12)
                pdf.cell(40, 10, str(campos[i + 1][1]), border=0)
            pdf.ln(8)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(35, 10, "Versão:", border=0)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, str(campos[-1][1]), border=0)

        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        contador += 1

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Total de veículos: {total_veiculos}", ln=True, align="C")

    pdf_path = "relatorio_carros.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')


@app.route('/relatorio/motos', methods=['GET'])
def criar_pdf_moto():
    cursor = con.cursor()
    cursor.execute("SELECT marca, modelo, placa, ano_modelo, ano_fabricacao, categoria, cor, renavam, marchas, partida, tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, alimentacao, versao, estado, cidade, quilometragem, preco_compra, preco_venda, licenciado FROM motos")
    motos = cursor.fetchall()
    cursor.close()

    total_veiculos = len(motos)

    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    motos_por_pagina = 3
    contador = 0

    for moto in motos:
        if contador == motos_por_pagina:
            pdf.add_page()
            contador = 0

        campos = [
            ("Marca", moto[0]), ("Modelo", moto[1]), ("Placa", moto[2]),
            ("Ano Modelo", moto[3]), ("Ano Fabricação", moto[4]), ("Categoria", moto[5]),
            ("Cor", moto[6]), ("Renavam", moto[7]), ("Marchas", moto[8]),
            ("Partida", moto[9]), ("Tipo do Motor", moto[10]), ("Cilindradas", moto[11]),
            ("Freio D/T", moto[12]), ("Refrigeração", moto[13]), ("Alimentação", moto[14]),
            ("Quilometragem", format_kilometragem(moto[18])), ("Estado", moto[16]), ("Cidade", moto[17]),
            ("Preço Compra", format_currency(moto[19])), ("Preço Venda", format_currency(moto[20])),
            ("Licenciado", "Sim" if moto[21] == 1 else "Não"), ("Versão", moto[15])
        ]

        for i in range(0, len(campos) - 1, 2):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(35, 10, f"{campos[i][0]}:", border=0)
            pdf.set_font("Arial", "", 12)
            pdf.cell(40, 10, str(campos[i][1]), border=0)

            if i + 1 < len(campos) - 1:
                pdf.set_x(120)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(35, 10, f"{campos[i + 1][0]}:", border=0)
                pdf.set_font("Arial", "", 12)
                pdf.cell(40, 10, str(campos[i + 1][1]), border=0)
            pdf.ln(8)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(35, 10, "Versão:", border=0)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, str(campos[-1][1]), border=0)

        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        contador += 1

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Total de veículos: {total_veiculos}", ln=True, align="C")

    pdf_path = "relatorio_motos.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')