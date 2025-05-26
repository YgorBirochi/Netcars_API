from flask import Flask, send_file, request, jsonify
from main import app, con
from fpdf import FPDF
from datetime import datetime
import re

# Funções de formatação

def format_none(value):
    return "Não informado" if value in [None, "none", "None"] else value

def format_currency(value):
    # Trata valores nulos ou inválidos
    if value in [None, "none", "None"]:
        return "Não informado"
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "Não informado"

def format_kilometragem(value):
    return f"{value:,} km".replace(",", ".")

def format_phone(phone):
    if phone is None:
        return None
    phone_str = str(phone)
    digits = re.sub(r'\D', '', phone_str)
    if len(digits) == 11:
        return f"({digits[0:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[0:2]}) {digits[2:6]}-{digits[6:]}"
    else:
        return phone_str


def format_cpf_cnpj(value):
    if value is None:
        return None
    value_str = str(value)
    digits = re.sub(r'\D', '', value_str)
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    elif len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    else:
        return value_str


def format_date(date_value):
    if date_value is None:
        return None
    if isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y')
    try:
        dt = datetime.strptime(str(date_value), '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except ValueError:
        return str(date_value)

# Fim das funções de formatação

# Ínicio das Classes
class CustomCarroPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_title("Relatório de Carros")
        self.set_author("Sistema de Concessionária")
        self.primary_color = (56, 56, 56)  # Cinza
        self.accent_color = (220, 50, 50)  # Vermelho para destaques


        # Dimensões
        self.card_height = 70   # Altura de cada card
        self.card_margin_x = 7.5 # Margem lateral
        self.card_width = 195  # Largura total do card
        self.line_height = 5    # Altura da linha de texto
        self.card_spacing = 15  # Espaço entre os cards
        self.normal_font_size = 10
        self.bold_font_size = 10

    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, "Relatório de Carros", 0, 1, "C")

        self.set_font("Arial", "", 10)
        self.cell(0, 6, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "C")

        self.ln(4)
        self.set_line_width(0.5)
        self.set_draw_color(*self.primary_color)
        # Linha horizontal
        self.line(10, 30, self.w - 10, 30)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

    def create_car_cards(self, carros):
        """
        Renderiza os cards de 3 em 3 por página e exibe o total
        no rodapé da última página.
        """
        self.alias_nb_pages()
        total_carros = len(carros)

        # 1) Se não houver carros, gera só uma página com mensagem + total
        if total_carros == 0:
            self.add_page()      # dispara header()
            self.ln(10)          # espaçamento após o header

            self.set_font("Arial", "", 12)
            self.cell(
                0, 10,
                "Nenhum carro encontrado para os critérios informados.",
                ln=True, align="C"
            )

            self.ln(8)
            self.set_font("Arial", "B", 14)
            self.cell(
                0, 10,
                f"Total de carros: {total_carros}",
                ln=True, align="C"
            )
            return

        # 2) Se houver carros, gera 3 cards por página
        for i, carro in enumerate(carros):
            # a cada 3 carros, abre página nova e reinicia current_page_y
            if i % 3 == 0:
                self.add_page()
                # get_y() já está posicionado logo abaixo do header()
                self.current_page_y = self.get_y()

            # calcula Y do card atual
            start_y = self.current_page_y + (i % 3) * (self.card_height + self.card_spacing)
            self._draw_card(carro, start_y)

            # se completou uma “fila” de 3, avança para a próxima linha
            if i % 3 == 2:
                self.current_page_y += self.card_height + self.card_spacing

        # 3) Na última página, exibe o total no rodapé (30 pts acima do final)
        self.set_y(-30)
        self.set_font("Arial", "B", 14)
        self.cell(
            0, 10,
            f"Total de carros: {total_carros}",
            ln=True, align="C"
        )

    def _draw_card(self, data, start_y):
        """Desenha um card na posição vertical 'start_y'."""
        # Fundo do card
        self.set_fill_color(240, 240, 240)
        self.rect(self.card_margin_x, start_y, self.card_width, self.card_height, "F")

        # Cabeçalho do card: Marca + Modelo
        self.set_xy(self.card_margin_x + 5, start_y + 5)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*self.primary_color)
        self.cell(0, 6, f"{data[0]} {data[1]}", ln=1)

        # Colunas
        col1_x = self.card_margin_x + 5
        col2_x = col1_x + 90  # ~90 px de distância da coluna 1
        y_left = start_y + 14
        y_right = start_y + 14

        # Coluna esquerda
        fields_left = [
            ("Placa", data[2]),
            ("Ano Modelo", data[3]),
            ("Cor", data[5]),
            ("Câmbio", data[7]),
            ("Preço Compra", format_currency(data[13])),
            ("Licenciado", "Sim" if data[15] == 1 else "Não")
        ]
        for label, value in fields_left:
            self.set_xy(col1_x, y_left)
            self.set_font("Arial", "", self.normal_font_size)
            self.cell(30, self.line_height, f"{label}:", 0, 0)
            self.set_font("Arial", "B", self.bold_font_size)
            self.cell(50, self.line_height, str(value), 0, 0)
            y_left += self.line_height + 1

        # Coluna direita
        fields_right = [
            ("Ano Fabricação", data[4]),
            ("Combustível", data[8]),
            ("Quilometragem", format_kilometragem(data[10])),
            ("Cidade/Estado", f"{data[12]}/{data[11]}"),
            ("Preço Venda", format_currency(data[14]))
        ]
        for label, value in fields_right:
            self.set_xy(col2_x, y_right)
            self.set_font("Arial", "", self.normal_font_size)
            self.cell(40, self.line_height, f"{label}:", 0, 0)
            self.set_font("Arial", "B", self.bold_font_size)
            self.cell(50, self.line_height, str(value), 0, 0)
            y_right += self.line_height + 1

        # Versão no rodapé do card
        versao_y = start_y + self.card_height - 20
        self.set_xy(col1_x, versao_y)
        self.set_font("Arial", "", self.normal_font_size)
        self.cell(30, self.line_height, "Versão:", 0, 0)
        self.set_font("Arial", "B", self.bold_font_size)
        self.cell(0, self.line_height, str(data[16]), 0, 0)

class CustomMotosPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_title("Relatório de Motos")
        self.set_author("Sistema de Veículos")
        self.primary_color = (56, 56, 56)  # Cinza
        self.accent_color = (220, 50, 50)  # Vermelho para destaques

        # Dimensões
        self.card_height = 70
        self.card_margin_x = 10
        self.card_width = 190
        self.line_height = 5
        self.card_spacing = 15
        self.normal_font_size = 10
        self.bold_font_size = 10

    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, "Relatório de Motos", 0, 1, "C")

        self.set_font("Arial", "", 10)
        self.cell(0, 6, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "C")

        self.ln(4)
        self.set_line_width(0.5)
        self.set_draw_color(*self.primary_color)
        # Linha horizontal
        self.line(10, 30, self.w - 10, 30)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

    def create_moto_cards(self, motos):
        """
        Renderiza os cards de motos em uma grade de 3 por página
        e exibe o total no rodapé da última página.
        """
        self.alias_nb_pages()
        total_motos = len(motos)

        # ——————————————————————————————————————————
        # 1) Se não houver motos, gera só uma página com mensagem + total
        if total_motos == 0:
            self.add_page()  # dispara header()
            self.ln(10)  # espaçamento após o header

            self.set_font("Arial", "", 12)
            self.cell(
                0, 10,
                "Nenhuma moto encontrada para os critérios informados.",
                ln=True, align="C"
            )

            self.ln(8)
            self.set_font("Arial", "B", 14)
            self.cell(
                0, 10,
                f"Total de motos: {total_motos}",
                ln=True, align="C"
            )
            return

        # ——————————————————————————————————————————
        # 2) Se houver motos, gera 3 cards por página
        for i, moto in enumerate(motos):
            # a cada 3 motos, abre página nova e reinicia current_page_y
            if i % 3 == 0:
                self.add_page()
                # get_y() já está posicionado logo abaixo do header()
                self.current_page_y = self.get_y()

            # posição vertical do card
            card_y = self.current_page_y + (i % 3) * (self.card_height + self.card_spacing)
            self._draw_card(moto, card_y)

            # se terminer uma “fila” de 3, avança para próxima linha
            if i % 3 == 2:
                self.current_page_y += self.card_height + self.card_spacing

        # ——————————————————————————————————————————
        # 3) Na última página, exibe o total no rodapé (30 pts acima do final)
        self.set_y(-30)
        self.set_font("Arial", "B", 14)
        self.cell(
            0, 10,
            f"Total de motos: {total_motos}",
            ln=True, align="C"
        )

    def _draw_card(self, data, start_y):
        """Desenha um card na posição vertical 'start_y'."""
        # Fundo do card
        self.set_fill_color(240, 240, 240)
        self.rect(self.card_margin_x, start_y, self.card_width, self.card_height, "F")

        # Cabeçalho do card: Marca + Modelo
        self.set_xy(self.card_margin_x + 5, start_y + 5)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*self.primary_color)
        self.cell(0, 6, f"{data[0]} {data[1]}", ln=1)

        # Colunas
        col1_x = self.card_margin_x + 5
        col2_x = col1_x + 90  # ~90 px de distância da coluna 1
        y_left = start_y + 14
        y_right = start_y + 14

        # Coluna esquerda
        fields_left = [
            ("Placa", data[2]),
            ("Ano Modelo", data[3]),
            ("Categoria", data[5]),
            ("Cor", data[6]),
            ("Marchas", data[8]),
            ("Licenciado", "Sim" if data[19] == 1 else "Não")
        ]
        for label, value in fields_left:
            self.set_xy(col1_x, y_left)
            self.set_font("Arial", "", self.normal_font_size)
            self.cell(30, self.line_height, f"{label}:", 0, 0)
            self.set_font("Arial", "B", self.bold_font_size)
            self.cell(50, self.line_height, str(value), 0, 0)
            y_left += self.line_height + 1

        # Coluna direita
        fields_right = [
            ("Ano Fabricação", data[4]),
            ("Cilindradas", data[11]),
            ("Quilometragem", format_kilometragem(data[17])),
            ("Preço Compra", format_currency(data[18])),
            ("Preço Venda", format_currency(data[19]))
        ]
        for label, value in fields_right:
            self.set_xy(col2_x, y_right)
            self.set_font("Arial", "", self.normal_font_size)
            self.cell(40, self.line_height, f"{label}:", 0, 0)
            self.set_font("Arial", "B", self.bold_font_size)
            self.cell(50, self.line_height, str(value), 0, 0)
            y_right += self.line_height + 1


class CustomUsuarioPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_title("Relatório de Usuários")
        self.set_author("Sistema de Usuários")
        self.primary_color = (56, 56, 56)  # Cinza
        self.accent_color = (220, 50, 50)  # Vermelho para destaques

        self.card_height = 50
        self.card_margin_x = 10
        self.card_width = 90
        self.card_spacing_x = 10
        self.card_spacing_y = 10
        self.line_height = 5
        self.normal_font_size = 10
        self.bold_font_size = 10

    def header(self):
        # Cabeçalho
        self.set_font("Arial", "B", 14)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, "Relatório de Usuários", 0, 1, "C")

        self.set_font("Arial", "", 10)
        self.cell(0, 6, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "C")

        # Adicionando espaço antes da linha
        self.ln(2)

        # Linha horizontal abaixo do texto
        self.set_line_width(0.5)
        self.set_draw_color(*self.primary_color)
        self.line(10, self.get_y() + 2, self.w - 10, self.get_y() + 2)

        # Espaço após a linha para começar os cards
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

    def create_usuario_cards(self, usuarios):
        """Renderiza os cards de usuários em uma grade de 2x4 (8 por página)."""
        self.alias_nb_pages()
        total_usuarios = len(usuarios)

        # ——————————————————————————————————————————
        # Caso não haja usuários, gera só uma página com mensagem e total
        if total_usuarios == 0:
            self.add_page()  # dispara header automaticamente
            self.ln(10)  # dá um espaçamento após o header

            self.set_font("Arial", "", 12)
            self.cell(0, 10, "Nenhum usuário encontrado para os critérios informados.", ln=True, align="C")

            self.ln(8)
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, f"Total de usuários: {total_usuarios}", ln=True, align="C")
            return

        # ——————————————————————————————————————————
        # Se chegou aqui, há pelo menos 1 usuário:

        for i, usuario in enumerate(usuarios):
            # Nova página a cada 8 cards
            if i % 8 == 0:
                self.add_page()
                self.current_page_y = 35  # posição inicial abaixo do header

            # Cálculo de linha e coluna (2 cols x 4 rows)
            row = (i % 8) // 2
            col = (i % 2)

            card_x = self.card_margin_x + col * (self.card_width + self.card_spacing_x)
            card_y = self.current_page_y + row * (self.card_height + self.card_spacing_y)

            self._draw_card(usuario, card_x, card_y)

        # ——————————————————————————————————————————
        # Por fim, no final da última página, exibe o total
        self.set_y(-30)  # 30 pts acima do footer
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, f"Total de usuários: {total_usuarios}", ln=True, align="C")

    def _draw_card(self, data, start_x, start_y):
        """Desenha um card na posição (start_x, start_y)."""
        # Fundo do card
        self.set_fill_color(240, 240, 240)
        self.rect(start_x, start_y, self.card_width, self.card_height, "F")

        # Cabeçalho do card: Nome
        self.set_xy(start_x + 5, start_y + 5)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*self.primary_color)
        nome_truncado = self._truncate_text(data[0], self.card_width - 10, "Arial", "B", 10)
        self.cell(self.card_width - 10, 6, nome_truncado, ln=1)

        # Informações do usuário
        y_pos = start_y + 14
        fields = [
            ("Email", self._truncate_text(data[1], self.card_width - 15, "Arial", "", 9)),
            ("Telefone", format_none(format_phone(data[2]))),
            ("CPF/CNPJ", format_none(format_cpf_cnpj(data[3]))),
            ("Nascimento", format_none(format_date(data[4]))),
            ("Ativo", "Sim" if data[5] == 1 else "Não")
        ]

        for label, value in fields:
            self.set_xy(start_x + 5, y_pos)
            self.set_font("Arial", "", 9)
            self.cell(30, self.line_height, f"{label}:", 0, 0)
            self.set_xy(start_x + 35, y_pos)
            self.set_font("Arial", "B", 9)
            self.cell(self.card_width - 40, self.line_height, str(value), 0, 0)
            y_pos += self.line_height + 1

    def _truncate_text(self, text, max_width, font_family, font_style, font_size):
        """Trunca o texto se ele exceder a largura máxima."""
        self.set_font(font_family, font_style, font_size)
        if self.get_string_width(text) <= max_width:
            return text

        # Trunca o texto
        for i in range(len(text), 0, -1):
            truncated = text[:i] + "..."
            if self.get_string_width(truncated) <= max_width:
                return truncated

        return "..."

class CustomManutencaoPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_title("Relatório de Manutenções")
        self.set_author("Sistema de Concessionária")
        # cores
        self.primary_color = (56, 56, 56)
        self.accent_color = (108, 29, 233)
        # fontes e altura de linha
        self.font_norm = 11
        self.font_bold = 12
        self.line_h = 6

    def header(self):
        # Título centralizado
        self.set_font("Arial", "B", 14)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, "Relatório de Manutenção", ln=1, align='C')
        # Linha divisória
        self.set_line_width(0.5)
        self.set_draw_color(*self.primary_color)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align='C')

    def create_manutencao_report(self, manutencoes):
        self.alias_nb_pages()

        # Se não há manutenções, ou todas chegaram sem serviços, exibe mensagem única
        no_manut = (
            not manutencoes
            or all(len(m['servicos']) == 0 for m in manutencoes)
        )
        if no_manut:
            self.add_page()
            self.ln(20)
            self.set_font("Arial", "", 12)
            self.set_text_color(*self.primary_color)
            self.cell(
                0, 10,
                "Não há nenhuma manutenção para os critérios informados.",
                ln=True, align="C"
            )
            return

        # Caso haja ao menos uma manutenção com serviços, gera um relatório por manutenção
        for m in manutencoes:
            self.add_page()
            self._draw_header_box(m)
            self.ln(8)
            self._draw_services_table(m['servicos'])

    def _draw_header_box(self, m):
        # Desenha retângulo geral de header
        self.set_draw_color(*self.primary_color)
        x0, y0 = self.get_x(), self.get_y()
        total_w = self.w - 20
        total_h = 30
        self.rect(x0, y0, total_w, total_h)

        col_w = total_w / 4
        # Primeira linha: Veículo e Data
        self.set_font("Arial", "B", self.font_bold)
        self.set_xy(x0 + 2, y0 + 2)
        self.cell(col_w, self.line_h, "Veículo:", border=0)
        self.set_font("Arial", "", self.font_norm)
        self.cell(col_w, self.line_h, f"{m['marca']} {m['modelo']}", border=0)
        self.set_font("Arial", "B", self.font_bold)
        self.cell(col_w, self.line_h, "Data:", border=0)
        self.set_font("Arial", "", self.font_norm)
        data_fmt = datetime.strptime(str(m['data_manutencao']), '%Y-%m-%d').strftime('%d/%m/%Y')
        self.cell(col_w, self.line_h, data_fmt, border=0, ln=1)

        # Segunda linha: Placa e Valor Total
        self.set_font("Arial", "B", self.font_bold)
        self.set_x(x0 + 2)
        self.cell(col_w, self.line_h, "Placa:", border=0)
        self.set_font("Arial", "", self.font_norm)
        self.cell(col_w, self.line_h, m.get('placa', '-'), border=0)
        self.set_font("Arial", "B", self.font_bold)
        self.cell(col_w, self.line_h, "Valor Total:", border=0)
        self.set_font("Arial", "", self.font_norm)
        valor_fmt = f"R$ {m.get('valor_total', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        self.cell(col_w, self.line_h, valor_fmt, border=0)

        # Terceira linha: Observação
        self.set_xy(x0 + 2, y0 + 2 + self.line_h * 2)
        self.set_font("Arial", "B", self.font_bold)
        self.cell(0, self.line_h, "Observação:", border=0)
        self.ln(self.line_h)
        self.set_font("Arial", "", self.font_norm)
        self.set_x(x0 + 2)
        self.multi_cell(total_w - 4, self.line_h, m.get('observacao') or '-')

    def _draw_services_table(self, servicos):
        # Cabeçalho da tabela
        self.set_font("Arial", "B", self.font_bold)
        self.set_fill_color(230, 215, 245)
        tbl_w = self.w - 20
        w_desc = tbl_w * 0.6
        w_unit = tbl_w * 0.13
        w_qtd = tbl_w * 0.13
        w_total = tbl_w * 0.14

        self.set_text_color(40, 40, 40)
        self.cell(w_desc, self.line_h, "Descrição", border=1, fill=True)
        self.cell(w_unit, self.line_h, "Vr Unit.", border=1, fill=True)
        self.cell(w_qtd, self.line_h, "Qtd.", border=1, fill=True)
        self.cell(w_total, self.line_h, "Total", border=1, fill=True, ln=1)

        # Linhas de serviços
        self.set_font("Arial", "", self.font_norm)
        self.set_text_color(*self.primary_color)
        for srv in servicos:
            self.cell(w_desc, self.line_h, srv.get('descricao', '-'), border=1)
            unit = f"R$ {srv.get('valor_unitario', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            self.cell(w_unit, self.line_h, unit, border=1)
            self.cell(w_qtd, self.line_h, str(srv.get('quantidade', 0)), border=1)
            tot = f"R$ {srv.get('total_item', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            self.cell(w_total, self.line_h, tot, border=1, ln=1)

        # Total geral
        self.set_font("Arial", "B", self.font_bold)
        self.cell(w_desc + w_unit + w_qtd, self.line_h, "Total Geral", border=1)
        total_val = sum(s.get('total_item', 0) for s in servicos)
        total_fmt = f"R$ {total_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        self.cell(w_total, self.line_h, total_fmt, border=1, ln=1)

    # Override para evitar NoneType no método interno de escape do FPDF
    def _escape(self, s):
        if s is None:
            return ''
        s = str(s)
        return (
            s.replace('\\', '\\\\')
             .replace(')', '\\)')
             .replace('(', '\\(')
             .replace('\r', '\\r')
        )


class CustomReceitaDespesaPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_title("Relatório de Receitas e Despesas")
        self.set_author("Sistema Financeiro")
        # Cores e dimensões
        self.primary_color = (56, 56, 56)
        self.accent_color = (0, 102, 204)
        self.line_height = 6
        # Larguras das colunas: Data, Tipo, Descrição, Valor
        self.col_widths = [30, 30, 100, 30]

    def header(self):
        # Título
        self.set_font("Arial", "B", 14)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, "Relatório de Receitas e Despesas", 0, 1, "C")

        # Data de geração
        self.set_font("Arial", "", 10)
        gerado = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.cell(0, 6, f"Gerado em: {gerado}", 0, 1, "C")
        self.ln(4)

        # Cabeçalho da tabela
        self._draw_table_header()

    def footer(self):
        # Rodapé com numeração
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

    def _draw_table_header(self):
        # Cabeçalho das colunas com alinhamentos distintos
        self.set_font("Arial", "B", 10)
        self.set_text_color(*self.primary_color)
        headers = ["Data", "Tipo", "Descrição", "Valor (R$)"]
        aligns  = ['C',    'C',    'L',           'R']
        for i, title in enumerate(headers):
            self.cell(self.col_widths[i], self.line_height, title, 1, 0, aligns[i])
        self.ln(self.line_height)

    def create_receita_despesa_list(self, registros):
        """Renderiza uma lista tabular de receitas e despesas."""
        self.alias_nb_pages()
        self.add_page()

        # Se não houver registros
        if not registros:
            self.set_font("Arial", "", 12)
            self.cell(0, 10, "Nenhum registro encontrado.", ln=True, align="C")
            return

        # Conteúdo da tabela
        self.set_font("Arial", "", 10)
        self.set_text_color(*self.primary_color)
        saldo = 0.0

        for reg in registros:
            # Quebra de página automática
            if self.get_y() > self.h - 30:
                self.add_page()

            data_str  = reg['data'].strftime('%d/%m/%Y')
            tipo_str  = reg['tipo']
            descricao = reg['descricao']
            valor_dec = reg['valor']          # geralmente Decimal vindo do DB
            valor_num = float(valor_dec)     # converte para float

            # Ajuste de saldo
            if tipo_str.lower() == 'receita':
                saldo += valor_num
            else:
                saldo -= valor_num

            # Células da linha
            # Data (centralizado)
            self.set_text_color(*self.primary_color)
            self.cell(self.col_widths[0], self.line_height, data_str, 1, 0, 'C')

            # Tipo (centralizado, colorido)
            if tipo_str.lower() == 'receita':
                self.set_text_color(0, 150, 0)  # verde
            else:
                self.set_text_color(200, 0, 0)  # vermelho
            self.cell(self.col_widths[1], self.line_height, tipo_str, 1, 0, 'C')

            # Restaurar cor padrão para as próximas células
            self.set_text_color(*self.primary_color)

            # Descrição (esquerda, truncada)
            desc_w = self.col_widths[2]
            text = descricao
            if self.get_string_width(text) > desc_w:
                while self.get_string_width(text + '...') > desc_w and len(text):
                    text = text[:-1]
                text += '...'
            self.cell(desc_w, self.line_height, text, 1, 0, 'L')

            # Valor (direita)
            valor_str = f"{valor_num:,.2f}"
            self.cell(self.col_widths[3], self.line_height, valor_str, 1, 0, 'R')

            self.ln(self.line_height)

        # Saldo final
        self.ln(4)
        self.set_font("Arial", "B", 12)
        saldo_str = f"{saldo:,.2f}"
        self.cell(0, 8, f"Saldo Final: R$ {saldo_str}", 0, 1, 'R')

class CustomParcelamentoPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_title("Relatório de Parcelamentos")
        self.set_author("Sistema Financeiro")

        # Cores
        self.primary_color = (33, 37, 41)  # quase preto
        self.accent_color = (108, 29, 233)  # roxo vivo para destaques de seções, se quiser
        self.header_bg = (230, 215, 245)  # roxo suave para cabeçalho da tabela
        self.row_alt_bg = (245, 245, 245)  # cinza suave para linhas alternadas

        # Altura de linha e largura de colunas
        self.line_h = 7
        self.col_widths = [20, 35, 35, 30, 30, 30]

        # Flag para controlar reaparecimento de cabeçalho da tabela
        self.in_table = False

        # Margem inferior para auto page break
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.in_table:
            # Só cabeçalho da tabela
            self._draw_table_header()
            return

        # Cabeçalho completo (título + data + linha)
        self.set_font("Arial", "B", 16)
        self.set_text_color(*self.primary_color)
        self.cell(0, 12, "Relatório de Parcelamentos", ln=1, align="C")

        self.set_font("Arial", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"Gerado em {datetime.now():%d/%m/%Y %H:%M}", ln=1, align="C")

        self.ln(2)
        self.set_draw_color(*self.primary_color)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

    def _draw_table_header(self):
        """Desenha o cabeçalho da tabela de parcelas (fundo roxo + texto branco)."""
        self.set_font("Arial", "B", 10)
        self.set_fill_color(*self.header_bg)
        self.set_text_color(40, 40, 40)
        headers = ["Parcela", "Vencimento", "Pagamento", "Valor (R$)", "Amortização", "Status"]
        aligns = ["C", "C", "C", "R", "R", "C"]
        for w, h, a in zip(self.col_widths, headers, aligns):
            self.cell(w, self.line_h, h, border=1, align=a, fill=True)
        self.ln(self.line_h)
        # retorna cor de texto para dados
        self.set_text_color(*self.primary_color)

    def add_parcelamento(self, dados):
        # Inicie nova página / reset de contexto
        self.add_page()
        self.alias_nb_pages()

        # ——————————————————————————————————————————————
        # 1) Seção de 3 colunas: Cliente | Veículo | Financiamento
        usable_width = self.w - 20
        col_w = usable_width / 3

        # Títulos das colunas
        self.set_font("Arial", "B", 12)
        self.set_text_color(*self.primary_color)
        self.cell(col_w, self.line_h, "Dados do Cliente", ln=0)
        self.cell(col_w, self.line_h, "Veículo", ln=0)
        self.cell(col_w, self.line_h, "Financiamento", ln=1)

        # Conteúdo das colunas
        self.set_font("Arial", "", 10)
        self.set_text_color(33, 37, 41)
        cli = dados['cliente']
        v = dados['veiculo']
        total = format_currency(dados['total'])
        entrada = format_currency(dados['entrada'])
        qtd = f"{dados['qnt_parcelas']}x"

        # 1ª linha
        self.cell(col_w, self.line_h, f"Nome: {cli['nome']}", ln=0)
        self.cell(col_w, self.line_h, f"{v['marca']} {v['modelo']}", ln=0)
        self.cell(col_w, self.line_h, f"Total: {total}", ln=1)

        # 2ª linha
        self.cell(col_w, self.line_h, f"CPF/CNPJ: {format_cpf_cnpj(cli['cpf_cnpj'])}", ln=0)
        self.cell(col_w, self.line_h, f"Placa: {v['placa']}", ln=0)
        self.cell(col_w, self.line_h, f"Entrada: {entrada}", ln=1)

        # 3ª linha
        self.cell(col_w, self.line_h, f"Telefone: {format_phone(cli['telefone'])}", ln=0)
        self.cell(col_w, self.line_h, f"Ano: {v['ano_modelo']}/{v['ano_fabricacao']}", ln=0)
        self.cell(col_w, self.line_h, f"Parcelas: {qtd}", ln=1)

        self.ln(8)

        # ——————————————————————————————————————————————
        # 2) Tabela de Parcelas
        self.in_table = True
        self._draw_table_header()

        status_map = {1: "Pendente", 2: "Vencida", 3: "Paga", 4: "Amortizada"}
        self.set_font("Arial", "", 9)

        for i, p in enumerate(dados['parcelas']):
            # Em cada nova linha, verifica se entrou em nova página:
            # se o y ultrapassar o limite, o header() vai redesenhar só o cabeçalho da tabela.
            fill = (i % 2 == 0)
            if fill:
                self.set_fill_color(*self.row_alt_bg)

            vals = [
                str(p['num']),
                format_date(p['venc']),
                format_date(p['pag']) if p['pag'] else "-",
                format_currency(p['valor']),
                format_currency(p['amort']),
                status_map.get(p['status'], str(p['status']))
            ]

            for w, txt, align in zip(self.col_widths, vals, ["C", "C", "C", "R", "R", "C"]):
                self.cell(w, self.line_h, txt, border=1, align=align, fill=fill)
            self.ln(self.line_h)

        # Finaliza a tabela antes do próximo parcelamento
        self.in_table = False
        self.ln(6)

class CustomClientesComprasPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_title("Relatório de Clientes e Compras")
        self.set_author("Sistema de Relatórios")
        # cores semelhantes ao PDF de manutenção
        self.primary_color = (56, 56, 56)
        self.accent_color = (230, 213, 245)
        self.accent_background = (230, 215, 245)
        # fontes e alturas
        self.font_norm = 11
        self.font_bold = 12
        self.line_h = 6

    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, "Relatório de Clientes e Compras", ln=1, align='C')
        self.set_line_width(0.5)
        self.set_draw_color(*self.primary_color)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align='C')

    def create_clientes_compras_list(self, clientes):
        self.alias_nb_pages()
        total_veiculos = 0
        soma_total = 0

        if not clientes:
            self.add_page()
            self.set_font("Arial", "", 12)
            self.cell(0, 10, "Nenhum cliente com compra encontrado.", ln=True, align='C')
            return

        for dados in clientes.values():
            compras = dados.get('compras', [])
            total_veiculos += len(compras)
            soma_total += sum(c.get('valor_total', 0) for c in compras)

            self.add_page()
            self._draw_cliente_header(dados)
            self.ln(4)
            self._draw_compras_section(compras)

        # total geral ao final
        self.set_y(-20)
        self.set_font("Arial", "B", 12)
        texto = f"Quantidade de compras: {total_veiculos}"
        texto2 = f"Valor total em compras: {format_currency(soma_total)}"
        self.cell(0, 10, texto, 0, 1, 'C')  # '1' aqui cria a quebra de linha
        self.cell(0, 10, texto2, 0, 0, 'C')

    def _draw_cliente_header(self, dados):
        x0, y0 = 10, self.get_y()
        box_w = self.w - 20

        # Parâmetros de espaçamento
        gap_entre_linhas = 2
        padding_superior = 2
        padding_inferior = 2
        linha_altura = self.line_h
        num_linhas = 2

        # Calcula altura do box
        box_h = padding_superior + num_linhas * linha_altura + gap_entre_linhas + padding_inferior
        col_w = box_w / 3

        # Desenha o retângulo
        self.set_draw_color(*self.primary_color)
        self.rect(x0, y0, box_w, box_h)

        # ─── Linha 1: Nome (maior e em negrito) │ Email (normal) │ CPF ───
        y_linha1 = y0 + padding_superior

        # Nome: Arial B, tamanho aumentado (+2)
        self.set_xy(x0 + 2, y_linha1)
        self.set_font("Arial", "B", self.font_bold + 2)
        self.set_text_color(*self.primary_color)
        self.cell(col_w, linha_altura + 1, dados['nome'], border=0)

        # Email: Arial normal, tamanho padrão
        self.set_xy(x0 + col_w + 2, y_linha1)
        self.set_font("Arial", "", self.font_norm)  # sem negrito
        self.cell(col_w, linha_altura + 1, dados['email'], border=0)

        # CPF/CNPJ
        self.set_xy(x0 + 2 * col_w + 2, y_linha1)
        self.set_font("Arial", "", self.font_norm)
        self.cell(col_w, linha_altura + 1,
                  f"CPF/CNPJ: {format_cpf_cnpj(dados['cpf_cnpj'])}",
                  border=0)

        # ─── Linha 2: Telefone │ Nascimento │ Cliente desde ───
        y_linha2 = y_linha1 + linha_altura + gap_entre_linhas + 1
        self.set_xy(x0 + 2, y_linha2)
        self.set_font("Arial", "", self.font_norm)
        self.set_text_color(*self.primary_color)
        self.cell(col_w, linha_altura, f"Telefone: {format_phone(dados['telefone'])}", border=0)
        self.set_xy(x0 + col_w + 2, y_linha2)
        self.cell(col_w, linha_altura, f"Nascimento: {format_date(dados['nascimento'])}", border=0)
        self.set_xy(x0 + 2 * col_w + 2, y_linha2)
        self.cell(col_w, linha_altura, f"Cliente desde: {format_date(dados['cliente_desde'])}", border=0)

        # Posiciona o cursor abaixo do box
        self.set_y(y0 + box_h + padding_inferior)

    def _draw_compras_section(self, compras):
        if not compras:
            return

        self.set_font("Arial", "B", self.font_bold)
        self.set_text_color(40, 40, 40)
        self.cell(0, self.line_h, "Compras", ln=1, align='C')
        self.ln(4)
        self.set_text_color(*self.primary_color)

        col_w = (self.w - 20) / 3
        x0 = 10

        total_valor = 0
        num_veiculos = len(compras)

        for idx, compra in enumerate(compras):
            # ─ Mini-cabeçalho Linha 1 ─
            self.set_xy(x0, self.get_y())
            self.set_fill_color(*self.accent_background)
            self.set_text_color(40, 40, 40)
            self.set_font("Arial", "B", self.font_bold)
            for label in ("Tipo Veículo", "Veículo", "Data Venda"):
                self.cell(col_w, self.line_h, label, border=1, fill=True, align='C')
            self.ln(self.line_h)

            # Dados Linha 1
            self.set_x(x0)
            self.set_font("Arial", "", self.font_norm)
            self.set_text_color(*self.primary_color)
            self.cell(col_w, self.line_h, str(compra.get('tipo_veiculo', '')), border=1, align='C')
            veic = f"{compra.get('marca', '')} {compra.get('modelo', '')} {compra.get('ano_modelo', '')}".strip()
            self.cell(col_w, self.line_h, veic, border=1, align='C')
            data_fmt = format_date(compra.get('data_venda')) if compra.get('data_venda') else ''
            self.cell(col_w, self.line_h, data_fmt, border=1, align='C')
            self.ln(self.line_h)

            # ─ Mini-cabeçalho Linha 2 ─
            self.set_x(x0)
            self.set_fill_color(*self.accent_background)
            self.set_text_color(40, 40, 40)
            self.set_font("Arial", "B", self.font_bold)
            for label in ("Placa", "Cor", "Forma Pagamento"):
                self.cell(col_w, self.line_h, label, border=1, fill=True, align='C')
            self.ln(self.line_h)

            # Dados Linha 2
            self.set_x(x0)
            self.set_font("Arial", "", self.font_norm)
            self.set_text_color(*self.primary_color)
            self.cell(col_w, self.line_h, str(compra.get('placa', '')), border=1, align='C')
            self.cell(col_w, self.line_h, str(compra.get('cor', '')), border=1, align='C')
            self.cell(col_w, self.line_h, str(compra.get('forma_pagamento', '')), border=1, align='C')
            self.ln(self.line_h)

            # ─ Mini-cabeçalho Linha 3 ─
            self.set_x(x0)
            self.set_fill_color(*self.accent_background)
            self.set_text_color(40, 40, 40)
            self.set_font("Arial", "B", self.font_bold)
            for label in ("Valor Entrada", "Valor Em Aberto", "Valor Pago"):
                self.cell(col_w, self.line_h, label, border=1, fill=True, align='C')
            self.ln(self.line_h)

            # Dados Linha 3
            self.set_x(x0)
            self.set_font("Arial", "", self.font_norm)
            self.set_text_color(*self.primary_color)
            entrada = compra.get('entrada', 0)
            aberto = compra.get('valor_fin_aberto', 0)
            pago = compra.get('valor_fin_pago', 0)
            valor_total_veiculo = compra.get('valor_total', 0)
            total_valor += valor_total_veiculo
            self.cell(col_w, self.line_h, format_currency(entrada), border=1, align='C')
            self.cell(col_w, self.line_h, format_currency(aberto), border=1, align='C')
            self.cell(col_w, self.line_h, format_currency(pago), border=1, align='C')
            self.ln(self.line_h + 2)

            self.ln(10)

            # ─ Totalizador ao final da última tabela ─
            if idx == num_veiculos - 1:
                self.set_font("Arial", "B", self.font_bold)
                self.set_text_color(*self.primary_color)
                plural = "veículo" if num_veiculos == 1 else "veículos"

                # Linha 1: Quantidade de veículos
                self.cell(
                    0,
                    self.line_h,
                    f"Quantidade de veículos: {num_veiculos}",
                    ln=1,
                    align='R'
                )

                # Linha 2: Valor total
                self.cell(
                    0,
                    self.line_h,
                    f"Valor total em compras: {format_currency(total_valor)}",
                    ln=1,
                    align='R'
                )

                self.ln(5)

    # Override para evitar NoneType no método interno de escape do FPDF
    def _escape(self, s):
        if s is None:
            return ''
        s = str(s)
        return (
            s.replace('\\', '\\\\')
            .replace(')', '\\)')
            .replace('(', '\\(')
            .replace('\r', '\\r')
        )


# Fim das Classes

# Início das Rotas

# Relatorio de Carros
@app.route('/relatorio/carros', methods=['GET'])
def criar_pdf_carro():
    marca = request.args.get('marca')
    ano_fabricacao = request.args.get('ano_fabricacao')
    ano_modelo = request.args.get('ano_modelo')

    query = """SELECT marca, modelo, placa, ano_modelo, ano_fabricacao, cor, renavam, cambio, combustivel, 
                      categoria, quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, versao 
               FROM carros WHERE 1=1"""
    params = []
    if marca:
        query += " AND UPPER(marca) = UPPER(?)"
        params.append(marca)
    if ano_fabricacao and ano_modelo:
        query += " AND ano_fabricacao = ? AND ano_modelo = ?"
        params.extend([ano_fabricacao, ano_modelo])
    elif ano_fabricacao:
        query += " AND ano_fabricacao = ?"
        params.append(ano_fabricacao)
    elif ano_modelo:
        query += " AND ano_modelo = ?"
        params.append(ano_modelo)

    cursor = con.cursor()
    cursor.execute(query, params)
    carros = cursor.fetchall()
    cursor.close()

    pdf = CustomCarroPDF()
    pdf.create_car_cards(carros)  # Gera os cards dos carros e adiciona o total na última página
    pdf_path = "relatorio_carros.pdf"
    pdf.output(pdf_path)
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"Relatorio_Carros_{datetime.now().strftime('%Y%m%d')}.pdf"
    )

# Relatorio de Motos
@app.route('/relatorio/motos', methods=['GET'])
def criar_pdf_moto():
    marca = request.args.get('marca')
    ano_fabricacao = request.args.get('ano_fabricacao')
    ano_modelo = request.args.get('ano_modelo')

    # Removida a coluna "versao" da consulta, já que parece não existir na tabela motos
    query = """SELECT marca, modelo, placa, ano_modelo, ano_fabricacao, categoria, cor, renavam, 
                      marchas, partida, tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, 
                      alimentacao, estado, cidade, quilometragem, preco_compra, preco_venda, licenciado 
               FROM motos WHERE 1=1"""
    params = []

    if marca:
        query += " AND UPPER(marca) = UPPER(?)"
        params.append(marca)

    if ano_fabricacao and ano_modelo:
        query += " AND ano_fabricacao = ? AND ano_modelo = ?"
        params.extend([ano_fabricacao, ano_modelo])
    elif ano_fabricacao:
        query += " AND ano_fabricacao = ?"
        params.append(ano_fabricacao)
    elif ano_modelo:
        query += " AND ano_modelo = ?"
        params.append(ano_modelo)

    cursor = con.cursor()
    cursor.execute(query, params)
    motos = cursor.fetchall()
    cursor.close()

    # Vamos adicionar um valor padrão para o campo "versao" que está sendo usado no _draw_card
    motos_com_versao = []
    for moto in motos:
        # Convertemos a tupla para lista, adicionamos o valor padrão de versão, e convertemos de volta para tupla
        moto_lista = list(moto)
        moto_lista.append("N/A")  # Adiciona um valor padrão para versão
        motos_com_versao.append(tuple(moto_lista))

    pdf = CustomMotosPDF()
    pdf.create_moto_cards(motos_com_versao)  # Usa o método create_moto_cards com os dados ajustados
    pdf_path = "relatorio_motos.pdf"
    pdf.output(pdf_path)
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"Relatorio_Motos_{datetime.now().strftime('%Y%m%d')}.pdf"
    )

# Relatorio de Usuarios
@app.route('/relatorio/usuarios', methods=['GET'])
def criar_pdf_usuarios():
    # Obtendo parâmetros de filtro via query string
    nome = request.args.get('nome', '').strip()
    cpf_cnpj = request.args.get('cpf_cnpj', '').strip()
    dia = request.args.get('dia', '').strip()
    mes = request.args.get('mes', '').strip()
    ano = request.args.get('ano', '').strip()
    ativo = request.args.get('ativo', '').strip()

    if ativo.lower() == "ativo":
        ativo = 1
    elif ativo.lower() == "inativo":
        ativo = 0

    # Monta a query com todos os campos, mas adiciona os filtros se forem informados
    query = """
        SELECT 
            nome_completo,
            email,
            telefone,
            cpf_cnpj,
            data_nascimento,
            ativo
        FROM usuario
        WHERE 1=1
    """
    params = []

    # Filtro por nome (busca parcial, sem distinção de caixa)
    if nome:
        query += " AND UPPER(nome_completo) LIKE ?"
        params.append('%' + nome.upper() + '%')

    # Filtro por CPF/CNPJ (busca parcial)
    if cpf_cnpj:
        query += " AND UPPER(cpf_cnpj) LIKE ?"
        params.append('%' + cpf_cnpj.upper() + '%')

    # Filtro por data de nascimento usando EXTRACT para dia, mês e ano
    if dia:
        query += " AND EXTRACT(DAY FROM data_nascimento) = ?"
        params.append(int(dia))
    if mes:
        query += " AND EXTRACT(MONTH FROM data_nascimento) = ?"
        params.append(int(mes))
    if ano:
        query += " AND EXTRACT(YEAR FROM data_nascimento) = ?"
        params.append(int(ano))

    # Filtro por status (ativo)
    if ativo in [0, 1]:
        query += " AND ativo = ?"
        params.append(int(ativo))

    cursor = con.cursor()
    cursor.execute(query, params)
    usuarios = cursor.fetchall()
    cursor.close()

    pdf = CustomUsuarioPDF()
    pdf.create_usuario_cards(usuarios)  # Usa o método create_usuario_cards já implementado
    pdf_path = "relatorio_usuarios.pdf"
    pdf.output(pdf_path)
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"Relatorio_Usuarios_{datetime.now().strftime('%Y%m%d')}.pdf"
    )

# Relatorio de Manutenções
@app.route('/relatorio/manutencao', methods=['GET'])
def criar_pdf_manutencao():
    tipo_veic = request.args.get('tipo-veic', '').strip()
    dia = request.args.get('dia', '').strip()
    mes = request.args.get('mes', '').strip()
    ano = request.args.get('ano', '').strip()
    id_manutencao = request.args.get('id', '').strip()

    # Query principal
    query = """
        SELECT m.ID_MANUTENCAO,
               m.ID_VEICULO,
               m.TIPO_VEICULO,
               m.DATA_MANUTENCAO,
               m.OBSERVACAO,
               m.VALOR_TOTAL,
               ms.QUANTIDADE U,
               ms.VALOR_TOTAL_ITEM,
               s.DESCRICAO,
               s.VALOR
          FROM MANUTENCAO m
          LEFT JOIN MANUTENCAO_SERVICOS ms ON ms.ID_MANUTENCAO = m.ID_MANUTENCAO
          LEFT JOIN SERVICOS s ON s.ID_SERVICOS = ms.ID_SERVICOS
         WHERE m.ATIVO = TRUE
    """

    params = []

    if id_manutencao:
        query += " AND m.ID_MANUTENCAO = ?"
        params.append(id_manutencao)
    else:
        if tipo_veic.lower() == 'carros':
            query += " AND m.TIPO_VEICULO = ?"
            params.append(1)
        elif tipo_veic.lower() == 'motos':
            query += " AND m.TIPO_VEICULO = ?"
            params.append(2)
        if dia:
            query += " AND EXTRACT(DAY FROM m.DATA_MANUTENCAO) = ?"
            params.append(int(dia))
        if mes:
            query += " AND EXTRACT(MONTH FROM m.DATA_MANUTENCAO) = ?"
            params.append(int(mes))
        if ano:
            query += " AND EXTRACT(YEAR FROM m.DATA_MANUTENCAO) = ?"
            params.append(int(ano))

    cursor = con.cursor()

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()

    # Agrupa manutenções, serviços e busca detalhes do veículo
    temp = {}
    for id_m, id_v, tp, dt, obs, val, quantidade, valor_item, desc, valor in rows:
        if id_m not in temp:
            # busca dados do veículo
            vc = con.cursor()
            if tp == 1:
                vc.execute('SELECT marca, modelo, ano_fabricacao, ano_modelo, placa FROM CARROS WHERE ID_CARRO = ?', (id_v,))
            else:
                vc.execute('SELECT marca, modelo, ano_fabricacao, ano_modelo, placa FROM MOTOS WHERE ID_MOTO = ?', (id_v,))
            veh = vc.fetchone() or (None, None, None, None, None)
            vc.close()
            temp[id_m] = {
                'id_manutencao': id_m,
                'id_veiculo': id_v,
                'tipo_veiculo': tp,
                'data_manutencao': dt,
                'observacao': obs,
                'valor_total': val,
                'marca': veh[0],
                'modelo': veh[1],
                'ano_fabricacao': veh[2],
                'ano_modelo': veh[3],
                'placa': veh[4],
                'servicos': []
            }
        # adiciona serviço se existir
        if desc:
            temp[id_m]['servicos'].append({
                'descricao': desc,
                'valor_unitario': float(valor) if valor is not None else 0.0,
                'quantidade': int(quantidade) if quantidade is not None else 0,
                'total_item': float(valor_item) if valor_item is not None else 0.0
            })

    manutencoes = list(temp.values())

    # Gera PDF
    pdf = CustomManutencaoPDF()
    pdf.create_manutencao_report(manutencoes)
    filename = f"relatorio_manutencoes.pdf"
    pdf.output(filename)
    return send_file(
        filename,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=filename
    )

# Relatorio de Despesas e receitas
@app.route('/relatorio/receita_despesa', methods=['GET'])
def criar_pdf_receita_despesa():
    # Parâmetros de filtro
    tipo = request.args.get('tipo', '').strip().lower()  # 'receita' ou 'despesa'
    dia = request.args.get('dia', '').strip()
    mes = request.args.get('mes', '').strip()
    ano = request.args.get('ano', '').strip()
    origem = request.args.get('origem', '').strip()  # tabela de origem opcional

    # Query principal
    query = '''
        SELECT ID_RECEITA_DESPESA,
               TIPO,
               VALOR,
               DATA_RECEITA_DESPESA,
               DESCRICAO,
               ID_ORIGEM,
               TABELA_ORIGEM
          FROM RECEITA_DESPESA
         WHERE 1=1
    '''
    params = []

    if tipo in ('receita', 'despesa'):
        # supondo: 1 = receita, 2 = despesa
        codigo = 1 if tipo == 'receita' else 2
        query += ' AND TIPO = ?'
        params.append(codigo)

    if dia:
        query += ' AND EXTRACT(DAY FROM DATA_RECEITA_DESPESA) = ?'
        params.append(int(dia))
    if mes:
        query += ' AND EXTRACT(MONTH FROM DATA_RECEITA_DESPESA) = ?'
        params.append(int(mes))
    if ano:
        query += ' AND EXTRACT(YEAR FROM DATA_RECEITA_DESPESA) = ?'
        params.append(int(ano))
    if origem:
        query += ' AND TABELA_ORIGEM = ?'
        params.append(origem)

    cursor = con.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()

    # Estrutura para agrupar e formatar entradas
    registros = []
    for id_rd, tp, valor, data_rd, desc, id_origem, tabela_origem in rows:
        registros.append({
            'id': id_rd,
            'tipo': 'Receita' if tp == 1 else 'Despesa',
            'valor': valor,
            'data': data_rd,
            'descricao': desc,
            'origem': f"{tabela_origem} (ID: {id_origem})"
        })

    # Gera PDF
    pdf = CustomReceitaDespesaPDF()
    pdf.create_receita_despesa_list(registros)
    filename = f"relatorio_receita_despesa.pdf"
    pdf.output(filename)

    return send_file(
        filename,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=filename
    )

# Relatorio de Clientes e Compras
@app.route('/relatorio/cliente_compras', methods=['GET'])
def criar_pdf_clientes_compras():
    # Parâmetros de filtro (opcional)
    cliente = request.args.get('cliente', '').strip()
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()

    # Consulta SQL base
    query = '''
	SELECT PR_BUSCA_CLIENTE_COMPRA.ID_VENDA_COMPRA,
	PR_BUSCA_CLIENTE_COMPRA.DATA_VENDA_COMPRA,
	PR_BUSCA_CLIENTE_COMPRA.VALOR_TOTAL,
	CASE 
    WHEN PR_BUSCA_CLIENTE_COMPRA.TIPO_VEICULO = 1 THEN 'Carro'
    WHEN PR_BUSCA_CLIENTE_COMPRA.TIPO_VEICULO = 2 THEN 'Moto'
    ELSE 'Desconhecido'
	END AS TIPO_VEICULO,
	PR_BUSCA_CLIENTE_COMPRA.ID_USUARIO,
	PR_BUSCA_CLIENTE_COMPRA.MARCA,
	PR_BUSCA_CLIENTE_COMPRA.MODELO,
	PR_BUSCA_CLIENTE_COMPRA.ANO_MODELO,
	PR_BUSCA_CLIENTE_COMPRA.ANO_FABRICACAO,
	PR_BUSCA_CLIENTE_COMPRA.COR,
	PR_BUSCA_CLIENTE_COMPRA.PLACA,
	PR_BUSCA_CLIENTE_COMPRA.NOME_COMPLETO,
	PR_BUSCA_CLIENTE_COMPRA.DATA_NASCIMENTO,
	PR_BUSCA_CLIENTE_COMPRA.EMAIL,
	PR_BUSCA_CLIENTE_COMPRA.TELEFONE,
	PR_BUSCA_CLIENTE_COMPRA.CPF_CNPJ,
	PR_BUSCA_CLIENTE_COMPRA.DATA_CADASTRO,
	round(PR_BUSCA_CLIENTE_COMPRA.valor_fin_aberto,2) AS valor_fin_aberto,
    round(PR_BUSCA_CLIENTE_COMPRA.valor_fin_pago,2) AS valor_fin_pago,
    round(PR_BUSCA_CLIENTE_COMPRA.ENTRADA,2) AS ENTRADA,
    PR_BUSCA_CLIENTE_COMPRA.FORMA_PAGAMENTOo
	FROM PR_BUSCA_CLIENTE_COMPRA
	ORDER BY PR_BUSCA_CLIENTE_COMPRA.ID_USUARIO
    '''
    params = []

    # Aplicar filtros, se fornecidos
    if cliente:
        query += ' AND U.NOME LIKE ?'
        params.append(f'%{cliente}%')
    if data_inicio:
        query += ' AND VC.DATA_VENDA_COMPRA >= ?'
        params.append(data_inicio)
    if data_fim:
        query += ' AND VC.DATA_VENDA_COMPRA <= ?'
        params.append(data_fim)

    cursor = con.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()

    # Estruturar os dados agrupados por cliente
    clientes = {}
    for (
            id_venda, data_venda, valor_total,
            tipo_veiculo, id_usuario,
            marca, modelo, ano_modelo, ano_fabricacao,
            cor, placa, nome, nascimento, email, telefone,
            cpf_cnpj, data_cadastro,
            valor_fin_aberto, valor_fin_pago, entrada,
            forma_pagamento
    ) in rows:

        if id_usuario not in clientes:
            clientes[id_usuario] = {
                'nome': nome,
                'nascimento': nascimento,
                'email': email,
                'telefone': telefone,
                'cpf_cnpj': cpf_cnpj,
                'cliente_desde': data_cadastro,
                'compras': []
            }

        clientes[id_usuario]['compras'].append({
            'id_venda': id_venda,
            'data_venda': data_venda,
            'valor_total': valor_total,
            'modelo': modelo,
            'marca': marca,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'cor': cor,
            'placa': placa,
            'tipo_veiculo': tipo_veiculo,
            'valor_fin_aberto': valor_fin_aberto,
            'valor_fin_pago': valor_fin_pago,
            'entrada': entrada,
            'forma_pagamento': forma_pagamento
        })


    pdf = CustomClientesComprasPDF()
    pdf.create_clientes_compras_list(clientes)
    filename = 'relatorio_clientes_compras.pdf'
    pdf.output(filename)

    # Enviar o arquivo PDF como resposta
    return send_file(
        filename,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=filename
    )

@app.route('/relatorio/parcelamentos', methods=['GET'])
def criar_pdf_parcelamentos():
    q = request.args.get('q', '').strip()
    cursor = con.cursor()

    # SQL base com JOINs e COALESCE para uniformizar marca/modelo/placa
    base_sql = """
    SELECT
      f.ID_FINANCIAMENTO,
      f.ENTRADA,
      f.QNT_PARCELAS,
      f.TIPO_VEICULO,
      f.VALOR_TOTAL,
      u.NOME_COMPLETO,
      u.CPF_CNPJ,
      u.TELEFONE,
      COALESCE(c.MARCA, m.MARCA)   AS MARCA,
      COALESCE(c.MODELO, m.MODELO) AS MODELO,
      COALESCE(c.PLACA, m.PLACA)   AS PLACA,
      COALESCE(c.ANO_MODELO, m.ANO_MODELO) AS ANO_MODELO,
      COALESCE(c.ANO_FABRICACAO, m.ANO_FABRICACAO) AS ANO_FABRICACAO
    FROM FINANCIAMENTO f
    JOIN USUARIO u ON u.ID_USUARIO = f.ID_USUARIO
    LEFT JOIN CARROS c 
      ON f.TIPO_VEICULO = 1 
     AND f.ID_VEICULO   = c.ID_CARRO
    LEFT JOIN MOTOS m 
      ON f.TIPO_VEICULO = 2 
     AND f.ID_VEICULO   = m.ID_MOTO
    """

    params = []
    if q:
        base_sql += """
        WHERE
          u.NOME_COMPLETO              CONTAINING ?
        OR COALESCE(c.MARCA, m.MARCA)     CONTAINING ?
        OR COALESCE(c.MODELO, m.MODELO)   CONTAINING ?
        OR COALESCE(c.PLACA, m.PLACA)     CONTAINING ?
        """
        # Passa apenas 'byd', sem % e sem upper()
        params.extend([q] * 4)

    base_sql += " ORDER BY u.NOME_COMPLETO, f.ID_FINANCIAMENTO"

    cursor.execute(base_sql, params)
    fin_list = cursor.fetchall()

    if not fin_list:
        return jsonify({'error': 'Nenhum parcelamento encontrado.'}), 400

    pdf = CustomParcelamentoPDF()
    for (id_fin, entrada, qnt, tp, total,
         nome, cpf, tel, marca, modelo, placa, ano_modelo, ano_fabricacao) in fin_list:

        # Busca as parcelas desse financiamento
        cursor.execute("""
            SELECT NUM_PARCELA, DATA_VENCIMENTO, DATA_PAGAMENTO,
                   VALOR_PARCELA, VALOR_PARCELA_AMORTIZADA, STATUS
            FROM FINANCIAMENTO_PARCELA
            WHERE ID_FINANCIAMENTO = ?
              ORDER BY NUM_PARCELA
        """, (id_fin,))
        parcelas = [{
            'num':    row[0],
            'venc':   row[1],
            'pag':    row[2],
            'valor':  float(row[3]),
            'amort':  float(row[4]),
            'status': row[5]
        } for row in cursor.fetchall()]

        dados = {
            'cliente': {
                'nome': nome,
                'cpf_cnpj': cpf,
                'telefone': tel
            },
            'veiculo': {
                'marca': marca or "-",
                'modelo': modelo or "-",
                'placa': placa or "-",
                'ano_modelo': ano_modelo or "-",
                "ano_fabricacao": ano_fabricacao or "-"
            },
            'entrada':      float(entrada),
            'total':        float(total),
            'qnt_parcelas': qnt,
            'parcelas':     parcelas
        }
        pdf.add_parcelamento(dados)

    cursor.close()
    filename = f"relatorio_parcelamentos.pdf"
    pdf.output(filename)
    return send_file(
        filename,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=filename
    )