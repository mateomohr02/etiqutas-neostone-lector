"""Envío de ZPL crudo a la Zebra ZD220t por el spooler de Windows (USB)."""
from __future__ import annotations

import logging

import win32print

logger = logging.getLogger(__name__)


class PrinterError(RuntimeError):
    pass


def get_default_printer() -> str:
    name = win32print.GetDefaultPrinter()
    if not name:
        raise PrinterError("No hay una impresora predeterminada configurada en Windows.")
    return name


def send_zpl(zpl: str, printer_name: str | None = None) -> None:
    printer_name = printer_name or get_default_printer()
    payload = zpl.encode("utf-8")
    logger.info("Enviando %d bytes de ZPL a '%s'", len(payload), printer_name)
    try:
        hprinter = win32print.OpenPrinter(printer_name)
    except Exception as exc:
        logger.exception("No se pudo abrir la impresora '%s'", printer_name)
        raise PrinterError(f"No se pudo abrir la impresora '{printer_name}': {exc}") from exc

    try:
        hjob = win32print.StartDocPrinter(hprinter, 1, ("Etiqueta Neostone", None, "RAW"))
        logger.debug("Job de impresion iniciado: %s", hjob)
        try:
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, payload)
            win32print.EndPagePrinter(hprinter)
        finally:
            win32print.EndDocPrinter(hprinter)
        logger.info("ZPL enviado correctamente a '%s'", printer_name)
    except Exception as exc:
        logger.exception("Error al imprimir en '%s'", printer_name)
        raise PrinterError(f"Error al imprimir en '{printer_name}': {exc}") from exc
    finally:
        win32print.ClosePrinter(hprinter)
