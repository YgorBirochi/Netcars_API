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

# Classe personalizada para gerar o PDF de Manutenções
class CustomManutencaoPDF(FPDF) :
    def __init__(self):
        super().__init__()
        self.set_title("Relatório de Manutenções")
        self.set_author("Sistema de Concessionária")

        # cores
        self.primary_color = (56, 56, 56)  # Cinza
        self.accent_color = (220, 50, 50)  # Vermelho para destaques

        # layout 3 colunas × 2 linhas
        self.card_margin_x = 10
        self.card_margin_y = 40
        self.card_spacing_x = 8
        self.card_spacing_y = 8
        self.cols = 2
        self.rows = 2
        usable_w = self.w - 2*self.card_margin_x - (self.cols-1)*self.card_spacing_x
        self.card_w = usable_w/self.cols
        self.card_h = 90

        # fontes
        self.line_h = 6
        self.font_norm = 11
        self.font_bold = 12

    def header(self):
        self.set_font("Arial","B",14)
        self.set_text_color(*self.primary_color)
        self.cell(0,10,"Relatório de Manutenções",0,1,'C')
        self.set_font("Arial","",10)
        self.cell(0,6,f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",0,1,'C')
        self.ln(2)
        self.set_line_width(0.5)
        self.set_draw_color(*self.primary_color)
        self.line(self.card_margin_x,30,self.w-self.card_margin_x,30)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial","I",8)
        self.set_text_color(150,150,150)
        self.cell(0,10,f"Página {self.page_no()}/{{nb}}",0,0,'C')

    def create_manutencao_cards(self, manutencoes):
        """
        Renderiza cards de manutenção em grid 2×2. Se não houver dados,
        exibe apenas uma página com aviso e total = 0.
        """
        self.alias_nb_pages()
        total = len(manutencoes)

        # ——————————————————————————————————————————
        # Caso NÃO haja manutenções, gera só uma página com mensagem + total
        if total == 0:
            self.add_page()  # dispara header()
            self.ln(10)  # espaçamento após o header

            self.set_font("Arial", "", 12)
            self.cell(
                0, 10,
                "Nenhuma manutenção encontrada para os critérios informados.",
                ln=True, align="C"
            )

            self.ln(8)
            self.set_font("Arial", "B", 14)
            self.cell(
                0, 10,
                f"Total de manutenções: {total}",
                ln=True, align="C"
            )
            return

        # ——————————————————————————————————————————
        # Se houver dados, prepara grid
        per_page = self.cols * self.rows

        for i, m in enumerate(manutencoes):
            # nova página a cada per_page
            if i % per_page == 0:
                self.add_page()

            # coluna e linha dentro da página
            col = i % self.cols
            row = (i % per_page) // self.cols

            x = self.card_margin_x + col * (self.card_w + self.card_spacing_x)
            y = self.card_margin_y + row * (self.card_h + self.card_spacing_y)

            self._draw_card(m, x, y)

        # ——————————————————————————————————————————
        # Imprime o total na última página (20 pts acima do rodapé)
        self.set_xy(self.card_margin_x, self.h - 20)
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, f"Total de manutenções: {total}", 0, 0, 'C')

    def _draw_card(self, m, x, y):
        self.set_fill_color(240, 240, 240)
        self.rect(x, y, self.card_w, self.card_h, 'F')
        cx = x + 4
        cy = y + 6

        # tipo do veículo
        tp = 'Carro' if m['tipo_veiculo'] == 1 else 'Moto'
        self.set_xy(cx, cy)
        self.set_font("Arial", "B", self.font_bold)
        self.set_text_color(*self.primary_color)
        self.cell(0, self.line_h, f"{tp}:", 0, 1)

        # detalhes do veículo
        self.set_font("Arial", "", self.font_norm)
        info = [
            f"Marca/Modelo: {format_none(m.get('marca'))} {format_none(m.get('modelo'))}",
            f"Ano Fab.: {format_date(m.get('ano_fabricacao'))}",
            f"Ano Mod.: {format_date(m.get('ano_modelo'))}",
            f"Placa: {format_none(m.get('placa'))}"
        ]

        for line in info:
            cy += self.line_h + 1
            self.set_xy(cx, cy)
            self.cell(0, self.line_h, line, 0, 1)

        # valor
        cy += self.line_h + 2
        self.set_xy(cx, cy)
        self.set_font("Arial", "B", self.font_bold)
        self.cell(45, self.line_h, "Valor da manutenção:")
        self.set_font("Arial", "", self.font_norm)
        self.cell(0, self.line_h, format_currency(m['valor_total']), 0, 1)

        # data
        cy += self.line_h + 2
        self.set_xy(cx, cy)
        self.set_font("Arial", "B", self.font_bold)
        self.cell(12, self.line_h, "Data:")
        self.set_font("Arial", "", self.font_norm)
        self.cell(0, self.line_h, format_date(m['data_manutencao']), 0, 1)

        # observação
        cy += self.line_h + 2
        self.set_xy(cx, cy)
        self.set_font("Arial", "B", self.font_bold)
        self.cell(0, self.line_h, "Observação:")

        cy += self.line_h + 1
        self.set_xy(cx, cy)
        self.set_font("Arial", "", self.font_norm)

        before_obs_y = cy
        self.multi_cell(self.card_w - 8, self.line_h, format_none(m['observacao']))
        after_obs_y = self.get_y()

        if after_obs_y > y + self.card_h:
            self.card_h = after_obs_y - y + 6  # atualiza a altura do card dinamicamente


# Fim das Classes

# Início das Rotas

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

@app.route('/relatorio/manutencao', methods=['GET'])
def criar_pdf_manutencao():
    tipo_veic = request.args.get('tipo-veic', '').strip()  # '', 'Carros' ou 'Motos'
    dia = request.args.get('dia', '').strip()
    mes = request.args.get('mes', '').strip()
    ano = request.args.get('ano', '').strip()

    # Query base
    query = """
        SELECT ID_MANUTENCAO,
               ID_VEICULO,
               TIPO_VEICULO,
               DATA_MANUTENCAO,
               OBSERVACAO,
               VALOR_TOTAL
          FROM MANUTENCAO
         WHERE ATIVO = TRUE
    """
    params = []

    # Filtro por tipo de veículo
    if tipo_veic.lower() == 'carros':
        query += " AND TIPO_VEICULO = ?"
        params.append(1)
    elif tipo_veic.lower() == 'motos':
        query += " AND TIPO_VEICULO = ?"
        params.append(2)

    # Filtros por dia, mês e ano usando EXTRACT
    if dia:
        query += " AND EXTRACT(DAY   FROM DATA_MANUTENCAO) = ?"
        params.append(int(dia))
    if mes:
        query += " AND EXTRACT(MONTH FROM DATA_MANUTENCAO) = ?"
        params.append(int(mes))
    if ano:
        query += " AND EXTRACT(YEAR  FROM DATA_MANUTENCAO) = ?"
        params.append(int(ano))

    # Executa a consulta
    cursor = con.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()

    # Converte tuplas em dicionários
    manutencoes = []
    for id_m, id_v, tp, dt, obs, val in rows:
        c = con.cursor()
        if tp == 1:
            c.execute(
                'SELECT marca, modelo, ano_fabricacao, ano_modelo, placa '
                'FROM CARROS WHERE id_carro = ?', (id_v,)
            )
        else:
            c.execute(
                'SELECT marca, modelo, ano_fabricacao, ano_modelo, placa '
                'FROM MOTOS WHERE id_moto = ?', (id_v,)
            )
        veh = c.fetchone() or (None,)*5
        c.close()

        manutencoes.append({
            'id_manutencao':   id_m,
            'id_veiculo':      id_v,
            'tipo_veiculo':    tp,
            'data_manutencao': dt,
            'observacao':      obs,
            'valor_total':     val,
            'marca':           veh[0],
            'modelo':          veh[1],
            'ano_fabricacao':  veh[2],
            'ano_modelo':      veh[3],
            'placa':           veh[4],
        })

    # Gera o PDF — se a lista estiver vazia, seu create_manutencao_cards exibe a página única de "nenhuma manutenção"
    pdf = CustomManutencaoPDF()
    pdf.create_manutencao_cards(manutencoes)
    filename = "relatorio_manutencoes.pdf"
    pdf.output(filename)

    return send_file(
        filename,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"Relatorio_Manutencoes_{datetime.now():%Y%m%d}.pdf"
    )

# Fim das Rotas