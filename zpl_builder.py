"""Genera el ZPL de una etiqueta Neostone para la Zebra ZD220t (203dpi, 9,80x5,90cm, ^BQN para el QR).

IMPORTANTE: estas coordenadas y tamaños se calcularon matemáticamente a partir de las
especificaciones dadas (mm -> dots a 203dpi) y del layout ya validado en el preview HTML.
Van a necesitar un ajuste fino con la ZD220t real: magnificación del QR, oscuridad y
posiciones exactas de cada campo.
"""
from __future__ import annotations

import logging
import re

import qrcode
from qrcode.constants import ERROR_CORRECT_Q

from models import LabelData

logger = logging.getLogger(__name__)

DPI = 203
MM_PER_INCH = 25.4
DOTS_PER_MM = DPI / MM_PER_INCH

LABEL_WIDTH_MM = 98
LABEL_HEIGHT_MM = 59
MARGIN_MM = 4  # > 0,20cm de margen no imprimible del fabricante, ya lo cubre
PRINT_SPEED_IPS = 5  # 12,7 cm/s == 5 in/s exacto
DARKNESS = 5  # TODO: verificar/ajustar contra la impresora real
QR_MAGNIFICATION_MAX = 4  # TODO: ajustar según legibilidad real del QR impreso
QR_BOX_MM = 23
QR_ERROR_CORRECTION = ERROR_CORRECT_Q  # debe coincidir con la "Q" en ^FDQA,...

# Font 0 es escalable y permite fijar alto y ancho por separado: usamos eso para
# diferenciar el peso visual entre campos, sin depender de una fuente en negrita real.
# Ancho > alto = trazo más grueso (negrita); ancho < alto = trazo más fino.
FONT_BOLD_WIDTH_RATIO = 1.15  # Cliente y Dimensiones: los campos a destacar
FONT_THIN_WIDTH_RATIO = 0.70  # resto de los campos (menos el QR)

_ESCAPE_RE = re.compile(r"[\^~]")


def mm(valor_mm: float) -> int:
    return round(valor_mm * DOTS_PER_MM)


def font_bold(altura_mm: float) -> str:
    return f"{mm(altura_mm)},{mm(altura_mm * FONT_BOLD_WIDTH_RATIO)}"


def font_thin(altura_mm: float) -> str:
    return f"{mm(altura_mm)},{mm(altura_mm * FONT_THIN_WIDTH_RATIO)}"


def _esc(texto: str | None) -> str:
    """Evita que ^ o ~ dentro de un dato corten el ZPL."""
    return _ESCAPE_RE.sub("", texto or "")


def _calcular_qr_modulos(contenido: str) -> int:
    """Cantidad de módulos por lado del QR para este contenido puntual.

    La cantidad de módulos (y por lo tanto el tamaño impreso) depende de
    cuánto contenido tenga: una descripción larga genera un QR con más
    módulos que uno corto.
    """
    qr = qrcode.QRCode(error_correction=QR_ERROR_CORRECTION)
    qr.add_data(str(contenido or ""))
    qr.make(fit=True)
    return qr.modules_count


def _calcular_magnificacion_qr(modulos: int, max_box_dots: int) -> int:
    """Mayor magnificación entera que sigue entrando en el recuadro disponible.

    Con magnificación fija, un QR "grande" (más módulos) puede terminar
    excediendo el espacio reservado en la etiqueta, asi que la ajustamos
    según el contenido puntual de cada etiqueta.
    """
    magnificacion = max_box_dots // modulos
    return min(QR_MAGNIFICATION_MAX, max(1, magnificacion))


def build_label_zpl(data: LabelData) -> str:
    ancho_dots = mm(LABEL_WIDTH_MM)
    alto_dots = mm(LABEL_HEIGHT_MM)
    margen = mm(MARGIN_MM)
    ancho_contenido = ancho_dots - margen * 2

    cliente = _esc(data.cliente)
    poblacion = _esc(data.poblacion)
    pedido = _esc(data.pedido)
    descripcion = _esc(data.descripcion)
    id_escena = _esc(data.id_escena)
    contador = f"* {data.bulto}/{data.total_bultos}"

    # El QR va arriba a la derecha, a la altura del código de pedido, dejando abajo
    # todo el ancho libre para L/H/P.
    medidas_y = alto_dots - margen - mm(7)
    qr_row_y = margen + mm(14)
    qr_gap_inferior = mm(3)  # separación mínima entre el QR y la fila de medidas
    qr_gap_derecho = mm(2)  # separación mínima entre el texto y el QR
    qr_reserva_ancho = QR_BOX_MM + 2  # ancho a reservar en pedido/descripcion para el QR
    qr_box_max_dots = min(
        mm(QR_BOX_MM),
        medidas_y - qr_row_y - qr_gap_inferior,
        mm(qr_reserva_ancho) - qr_gap_derecho,
    )

    # El QR se regenera con el contador (bulto/total) ya actualizado según la
    # cantidad ingresada por el operario (ver LabelData.with_bulto), y su
    # magnificación se recalcula según cuánto contenido tenga esta etiqueta
    # puntual para no exceder QR_BOX_MM.
    qr_payload = data.to_qr()
    qr_modulos = _calcular_qr_modulos(qr_payload)
    qr_magnificacion = _calcular_magnificacion_qr(qr_modulos, qr_box_max_dots)
    qr_box_dots = qr_modulos * qr_magnificacion
    qr_x = ancho_dots - margen - qr_box_dots
    qr_y = qr_row_y

    modulo_mm = qr_magnificacion / DOTS_PER_MM
    logger.info(
        "QR bulto=%s/%s: %d caracteres, %d modulos/lado, magnificacion=%d "
        "(maxima=%d), modulo=%.3fmm, box=%dx%d dots, darkness=^MD%d",
        data.bulto, data.total_bultos, len(qr_payload), qr_modulos,
        qr_magnificacion, QR_MAGNIFICATION_MAX, modulo_mm, qr_box_dots, qr_box_dots,
        DARKNESS,
    )
    if modulo_mm < 0.33:
        logger.warning(
            "Modulo de QR muy chico (%.3fmm) para bulto=%s/%s: puede ser dificil "
            "de leer con un lector 2D de resolucion media/baja. Considerar bajar "
            "QR_ERROR_CORRECTION a 'M' o acortar el contenido del QR.",
            modulo_mm, data.bulto, data.total_bultos,
        )

    # Medidas L/H/P: ocupan todo el ancho disponible de la etiqueta. Cada columna
    # tiene la letra en fuente delgada y el valor en negrita; ^BQ no soporta mezclar
    # dos grosores en un mismo campo, por eso son 6 campos (letra + valor) en vez de
    # un solo ^FD.
    medida_altura_mm = 4.3
    grupo_ancho = ancho_contenido // 3
    letra_ancho = mm(4)  # ancho reservado para la letra L/H/P
    gap_ancho = mm(0.5)  # separación entre la letra y su valor
    valor_ancho = grupo_ancho - letra_ancho - gap_ancho

    campos_medidas: list[str] = []
    for indice, (letra, valor) in enumerate([
        ("L", data.medida_l), ("H", data.medida_h), ("P", data.medida_p),
    ]):
        x_grupo = margen + grupo_ancho * indice
        x_valor = x_grupo + letra_ancho + gap_ancho
        campos_medidas.append(
            f"^FO{x_grupo},{medidas_y}^A0N,{font_thin(medida_altura_mm)}^FD{letra}^FS"
        )
        campos_medidas.append(
            f"^FO{x_valor},{medidas_y}^A0N,{font_bold(medida_altura_mm)}"
            f"^FB{valor_ancho},1,0,L^FD{_esc(valor)}^FS"
        )

    return "\n".join([
        "^XA",
        "^CI28",  # UTF-8, para tildes/ñ

        f"^PW{ancho_dots}",
        f"^LL{alto_dots}",
        f"^PR{PRINT_SPEED_IPS}",
        f"^MD{DARKNESS}",

        # Contador de bultos (arriba a la derecha), con un * a su izquierda
        f"^FO{ancho_dots - margen - mm(23)},{margen}^A0N,{font_thin(4.1)}^FB{mm(23)},1,0,R^FD{contador}^FS",

        # Cliente (arriba a la izquierda): campo a destacar, más grande y en negrita
        f"^FO{margen},{margen}^A0N,{font_bold(5.5)}^FB{ancho_contenido - mm(23)},1,0,L^FD{cliente}^FS",

        # Poblacion (izquierda) + ID (derecha), misma fila
        f"^FO{margen},{margen + mm(8)}^A0N,{font_thin(3.5)}^FD{poblacion}^FS",
        f"^FO{ancho_dots - margen - mm(34)},{margen + mm(7)}^A0N,{font_thin(5.7)}^FB{mm(34)},1,0,R^FDID: {id_escena}^FS",

        # N. DE PEDIDO (etiqueta chica + valor). El valor lleva ancho limitado para no
        # pisar el QR, que comparte esta misma fila a la derecha.
        f"^FO{margen},{margen + mm(15)}^A0N,{font_thin(3.5)}^FDN. DE PEDIDO:^FS",
        (f"^FO{margen + mm(34)},{margen + mm(14)}^A0N,{font_thin(5.7)}"
         f"^FB{ancho_contenido - mm(34) - mm(qr_reserva_ancho)},1,0,L^FD{pedido}^FS"),

        # Descripcion (hasta 3 lineas), dejando lugar al QR a la derecha
        (f"^FO{margen},{margen + mm(23)}^A0N,{font_thin(3.8)}"
         f"^FB{ancho_contenido - mm(qr_reserva_ancho)},3,2,L^FD{descripcion}^FS"),

        # Medidas L/H/P (abajo, ocupando todo el ancho): letra en fuente delgada,
        # valor en negrita.
        *campos_medidas,

        # QR (arriba a la derecha), generado nativamente por la impresora, no como
        # imagen. Magnificación ajustada según el contenido, para no exceder QR_BOX_MM.
        f"^FO{qr_x},{qr_y}^BQN,2,{qr_magnificacion},M",
        f"^FDQA,{qr_payload}^FS",

        "^XZ",
    ]) + "\n"


def build_batch_zpl(data: LabelData, total_bultos: int) -> str:
    """Concatena el ZPL de las N etiquetas (1/N .. N/N) en un solo envío."""
    return "".join(
        build_label_zpl(data.with_bulto(bulto=i, total_bultos=total_bultos))
        for i in range(1, total_bultos + 1)
    )
