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
DARKNESS = 15  # TODO: verificar/ajustar contra la impresora real (arrancaba en 1, casi sin tinta)
QR_MAGNIFICATION_MAX = 4  # TODO: ajustar según legibilidad real del QR impreso
QR_BOX_MM = 22
QR_ERROR_CORRECTION = "Q"  # debe coincidir con la "Q" en ^FDQA,...

_ESCAPE_RE = re.compile(r"[\^~]")


def mm(valor_mm: float) -> int:
    return round(valor_mm * DOTS_PER_MM)


def _esc(texto: str | None) -> str:
    """Evita que ^ o ~ dentro de un dato corten el ZPL."""
    return _ESCAPE_RE.sub("", texto or "")


def _calcular_qr_modulos(contenido: str) -> int:
    """Cantidad de módulos por lado del QR para este contenido puntual.

    La cantidad de módulos (y por lo tanto el tamaño impreso) depende de
    cuánto contenido tenga: una descripción larga genera un QR con más
    módulos que uno corto.
    """
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_Q)
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
    medidas = f"L  {_esc(data.medida_l)}   H  {_esc(data.medida_h)}   P  {_esc(data.medida_p)}"

    # El QR se regenera con el contador (bulto/total) ya actualizado según
    # la cantidad ingresada por el operario (ver LabelData.with_bulto), y su
    # magnificación se recalcula según cuánto contenido tenga esta etiqueta
    # puntual para no exceder QR_BOX_MM.
    qr_payload = data.to_qr()
    qr_box_max_dots = mm(QR_BOX_MM)
    qr_modulos = _calcular_qr_modulos(qr_payload)
    qr_magnificacion = _calcular_magnificacion_qr(qr_modulos, qr_box_max_dots)
    qr_box_dots = qr_modulos * qr_magnificacion
    qr_x = ancho_dots - margen - qr_box_dots - mm(5)
    qr_y = alto_dots - margen - qr_box_dots - mm(5)
    ancho_medidas = qr_x - margen - mm(2)

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

    return "\n".join([
        "^XA",
        "^CI28",  # UTF-8, para tildes/ñ

        f"^PW{ancho_dots}",
        f"^LL{alto_dots}",
        f"^PR{PRINT_SPEED_IPS}",
        f"^MD{DARKNESS}",

        # Contador de bultos (arriba a la derecha), con un * a su izquierda
        f"^FO{ancho_dots - margen - mm(20)},{margen}^A0N,{mm(3.6)},{mm(3.6)}^FB{mm(20)},1,0,R^FD{contador}^FS",

        # Cliente (arriba a la izquierda, negrita/grande)
        f"^FO{margen},{margen}^A0N,{mm(4.3)},{mm(4.3)}^FB{ancho_contenido - mm(20)},1,0,L^FD{cliente}^FS",

        # Poblacion (izquierda) + ID (derecha), misma fila
        f"^FO{margen},{margen + mm(7)}^A0N,{mm(3)},{mm(3)}^FD{poblacion}^FS",
        f"^FO{ancho_dots - margen - mm(30)},{margen + mm(6)}^A0N,{mm(5)},{mm(5)}^FB{mm(30)},1,0,R^FDID: {id_escena}^FS",

        # N. DE PEDIDO (etiqueta chica + valor grande en negrita)
        f"^FO{margen},{margen + mm(13)}^A0N,{mm(3)},{mm(3)}^FDN. DE PEDIDO:^FS",
        f"^FO{margen + mm(30)},{margen + mm(12)}^A0N,{mm(5)},{mm(5)}^FD{pedido}^FS",

        # Descripcion (hasta 3 lineas), dejando lugar a "Accesorios" a la derecha
        f"^FO{margen},{margen + mm(20)}^A0N,{mm(3.3)},{mm(3.3)}^FB{ancho_contenido - mm(26)},3,2,L^FD{descripcion}^FS",

        # "Accesorios": texto fijo de plantilla, no viene de la base de datos
        f"^FO{ancho_dots - margen - mm(19)},{margen + mm(20)}^A0N,{mm(3)},{mm(3)}^FB{mm(19)},1,0,L^FDAccesorios^FS",

        # Medidas L/H/P (abajo a la izquierda, negrita)
        f"^FO{margen},{alto_dots - margen - mm(6)}^A0N,{mm(3.3)},{mm(3.3)}^FB{ancho_medidas},1,0,L^FD{medidas}^FS",

        # QR (abajo a la derecha), generado nativamente por la impresora, no como imagen.
        # Magnificación ajustada según el contenido, para no exceder QR_BOX_MM.
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
