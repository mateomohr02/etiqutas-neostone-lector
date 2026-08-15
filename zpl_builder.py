"""Genera el ZPL de una etiqueta Neostone para la Zebra GK420t.

Medidas de impresora (definidas por el usuario en el driver):
  Ancho 10,80 cm / Alto 7,00 cm, área no imprimible 0,20 cm a cada lado.
GK420t imprime a 203 dpi ~ 8 dots/mm, de ahí las conversiones de abajo.
Las coordenadas de layout son aproximadas: van a necesitar un ajuste fino
una vez probadas contra la impresora real (todas están como constantes
acá arriba para facilitar ese calibrado).
"""
from __future__ import annotations

from models import LabelData

DOTS_PER_MM = 8
LABEL_WIDTH_DOTS = round(108 * DOTS_PER_MM)   # 864
LABEL_HEIGHT_DOTS = round(70 * DOTS_PER_MM)   # 560
MARGIN_DOTS = round(2 * DOTS_PER_MM)          # 16 (0.20 cm no imprimible)

PRINT_SPEED_IPS = 5     # 12.7 cm/s
DARKNESS = 1            # ~SD00-30, valor pedido por el usuario

LEFT_X = MARGIN_DOTS
TEXT_MAX_X = LABEL_WIDTH_DOTS - MARGIN_DOTS

# Bloque de texto (columna izquierda), deja lugar al contador y al QR a la derecha
TEXT_BLOCK_WIDTH = 560

QR_X = 640
QR_Y = 260
QR_MAGNIFICATION = 5

COUNTER_X = 760
COUNTER_Y = 20
COUNTER_FONT = 55


def _esc(value: str) -> str:
    """Evita que ^ o ~ dentro de un dato corten el ZPL."""
    return value.replace("^", " ").replace("~", " ")


def build_label_zpl(data: LabelData) -> str:
    counter = f"{data.bulto}/{data.total_bultos}"
    qr_payload = data.to_qr()

    return "\n".join([
        "^XA",
        "^CI28",
        f"~SD{DARKNESS:02d}",
        f"^PR{PRINT_SPEED_IPS}",
        f"^PW{LABEL_WIDTH_DOTS}",
        f"^LL{LABEL_HEIGHT_DOTS}",
        "^LH0,0",

        # Cliente / arquitecto
        f"^FO{LEFT_X},15^A0N,42,42^FB{TEXT_BLOCK_WIDTH},1,0,L^FD{_esc(data.cliente)}^FS",

        # Poblacion (izq) + ID (der, alineado dentro del bloque de texto)
        f"^FO{LEFT_X},75^A0N,26,26^FD{_esc(data.poblacion)}^FS",
        f"^FO{LEFT_X},75^A0N,30,30^FB{TEXT_BLOCK_WIDTH},1,0,R^FDID: {_esc(data.id_escena)}^FS",

        # N. de pedido
        f"^FO{LEFT_X},115^A0N,30,30^FDN. DE PEDIDO: {_esc(data.pedido)}^FS",

        # Descripcion del articulo (hasta 3 lineas, wrap automatico)
        f"^FO{LEFT_X},165^A0N,28,28^FB{TEXT_BLOCK_WIDTH},3,4,L^FD{_esc(data.descripcion)}^FS",

        # Medidas, abajo a la izquierda
        (f"^FO{LEFT_X},{LABEL_HEIGHT_DOTS - 70}^A0N,32,32"
         f"^FDL {_esc(data.medida_l)}   H {_esc(data.medida_h)}   P {_esc(data.medida_p)}^FS"),

        # Contador de bultos, arriba a la derecha, con marco
        f"^FO{COUNTER_X - 15},{COUNTER_Y - 10}^GB110,70,3^FS",
        f"^FO{COUNTER_X},{COUNTER_Y}^A0N,{COUNTER_FONT},{COUNTER_FONT}^FD{counter}^FS",

        # QR con todos los datos de la etiqueta, abajo a la derecha
        f"^FO{QR_X},{QR_Y}^BQN,2,{QR_MAGNIFICATION}^FDLA,{qr_payload}^FS",

        "^XZ",
    ]) + "\n"


def build_batch_zpl(data: LabelData, total_bultos: int) -> str:
    """Concatena el ZPL de las N etiquetas (1/N .. N/N) en un solo envío."""
    return "".join(
        build_label_zpl(data.with_bulto(bulto=i, total_bultos=total_bultos))
        for i in range(1, total_bultos + 1)
    )
