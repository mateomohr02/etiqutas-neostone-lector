"""Envío de ZPL crudo a la Zebra GK420t por el spooler de Windows (USB)."""
from __future__ import annotations

import win32print


class PrinterError(RuntimeError):
    pass


def get_default_printer() -> str:
    name = win32print.GetDefaultPrinter()
    if not name:
        raise PrinterError("No hay una impresora predeterminada configurada en Windows.")
    return name


def send_zpl(zpl: str, printer_name: str | None = None) -> None:
    printer_name = printer_name or get_default_printer()
    try:
        hprinter = win32print.OpenPrinter(printer_name)
    except Exception as exc:
        raise PrinterError(f"No se pudo abrir la impresora '{printer_name}': {exc}") from exc

    try:
        hjob = win32print.StartDocPrinter(hprinter, 1, ("Etiqueta Neostone", None, "RAW"))
        try:
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, zpl.encode("utf-8"))
            win32print.EndPagePrinter(hprinter)
        finally:
            win32print.EndDocPrinter(hprinter)
    except Exception as exc:
        raise PrinterError(f"Error al imprimir en '{printer_name}': {exc}") from exc
    finally:
        win32print.ClosePrinter(hprinter)
