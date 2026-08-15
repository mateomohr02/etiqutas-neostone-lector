"""App de escritorio para reimprimir etiquetas Neostone en N bultos.

Flujo: pantalla con un único botón -> escaneo de QR (el lector USB
funciona como teclado) -> pide cantidad de bultos -> imprime sin
previsualización -> vuelve al inicio.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

from models import InvalidLabelQR, LabelData
from printer import PrinterError, send_zpl
from zpl_builder import build_batch_zpl

BG = "#0f172a"
BG_PANEL = "#1e293b"
FG = "#f1f5f9"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
DANGER = "#dc2626"
OK = "#16a34a"
MUTED = "#94a3b8"


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Etiquetas Neostone")
        self.geometry("900x560")
        self.configure(bg=BG)
        self.minsize(700, 480)

        self.font_title = tkfont.Font(family="Segoe UI", size=30, weight="bold")
        self.font_button = tkfont.Font(family="Segoe UI", size=26, weight="bold")
        self.font_body = tkfont.Font(family="Segoe UI", size=16)
        self.font_body_bold = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.font_qty = tkfont.Font(family="Segoe UI", size=48, weight="bold")

        self.current_label: LabelData | None = None
        self._scan_buffer = tk.StringVar()

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)

        self._build_home()

    # ---------- helpers ----------
    def _clear(self) -> None:
        for widget in self.container.winfo_children():
            widget.destroy()

    def _big_button(self, parent, text, command, bg=ACCENT, fg="white", font=None):
        btn = tk.Button(
            parent, text=text, command=command, font=font or self.font_button,
            bg=bg, fg=fg, activebackground=ACCENT_HOVER, activeforeground="white",
            bd=0, relief="flat", padx=30, pady=20, cursor="hand2",
        )
        return btn

    # ---------- pantalla 1: inicio ----------
    def _build_home(self) -> None:
        self._clear()
        self.current_label = None

        tk.Label(
            self.container, text="Etiquetas Neostone", font=self.font_title,
            bg=BG, fg=FG,
        ).pack(pady=(60, 10))

        tk.Label(
            self.container, text="Reimpresión de etiquetas por cantidad de bultos",
            font=self.font_body, bg=BG, fg=MUTED,
        ).pack(pady=(0, 40))

        scan_btn = self._big_button(
            self.container, "ESCANEAR ETIQUETA", self._build_scan, bg=ACCENT,
        )
        scan_btn.pack(ipadx=40, ipady=30)

    # ---------- pantalla 2: escaneo ----------
    def _build_scan(self) -> None:
        self._clear()
        self._scan_buffer.set("")

        tk.Label(
            self.container, text="Escaneá el código QR de la etiqueta",
            font=self.font_title, bg=BG, fg=FG, wraplength=760, justify="center",
        ).pack(pady=(80, 20))

        tk.Label(
            self.container, text="(apuntá la pistola lectora a la etiqueta)",
            font=self.font_body, bg=BG, fg=MUTED,
        ).pack(pady=(0, 40))

        self.scan_error_label = tk.Label(
            self.container, text="", font=self.font_body_bold, bg=BG, fg=DANGER,
        )
        self.scan_error_label.pack(pady=(0, 10))

        entry = tk.Entry(
            self.container, textvariable=self._scan_buffer, font=("Segoe UI", 1),
            bg=BG, fg=BG, insertbackground=BG, bd=0, highlightthickness=0,
        )
        entry.place(x=-500, y=-500)  # oculto pero enfocado: recibe el "tipeo" del lector
        entry.focus_set()
        entry.bind("<Return>", self._on_scan_submit)
        self._scan_entry = entry

        self._big_button(
            self.container, "Cancelar", self._build_home, bg=BG_PANEL, fg=FG,
        ).pack(pady=20, ipadx=20, ipady=10)

    def _on_scan_submit(self, _event=None) -> None:
        raw = self._scan_buffer.get()
        self._scan_buffer.set("")
        if not raw.strip():
            return
        try:
            self.current_label = LabelData.from_qr(raw)
        except InvalidLabelQR:
            self.scan_error_label.config(
                text="QR no reconocido. Escaneá una etiqueta Neostone válida."
            )
            self._scan_entry.focus_set()
            return
        self._build_quantity()

    # ---------- pantalla 3: cantidad de bultos ----------
    def _build_quantity(self) -> None:
        self._clear()
        data = self.current_label
        assert data is not None

        tk.Label(
            self.container, text=data.descripcion, font=self.font_body_bold,
            bg=BG, fg=FG, wraplength=800, justify="center",
        ).pack(pady=(40, 4))
        tk.Label(
            self.container, text=f"Pedido {data.pedido}  ·  ID {data.id_escena}",
            font=self.font_body, bg=BG, fg=MUTED,
        ).pack(pady=(0, 30))

        tk.Label(
            self.container, text="¿En cuántos bultos se separó este módulo?",
            font=self.font_body_bold, bg=BG, fg=FG,
        ).pack(pady=(0, 15))

        qty_frame = tk.Frame(self.container, bg=BG)
        qty_frame.pack(pady=10)

        self._qty_var = tk.IntVar(value=1)

        def change(delta: int) -> None:
            new_val = max(1, self._qty_var.get() + delta)
            self._qty_var.set(new_val)

        self._big_button(qty_frame, "−", lambda: change(-1), bg=BG_PANEL, fg=FG,
                          font=self.font_qty).grid(row=0, column=0, padx=20)
        tk.Label(
            qty_frame, textvariable=self._qty_var, font=self.font_qty, bg=BG, fg=FG,
            width=3, anchor="center",
        ).grid(row=0, column=1, padx=20)
        self._big_button(qty_frame, "+", lambda: change(1), bg=BG_PANEL, fg=FG,
                          font=self.font_qty).grid(row=0, column=2, padx=20)

        self.print_error_label = tk.Label(
            self.container, text="", font=self.font_body_bold, bg=BG, fg=DANGER,
            wraplength=800, justify="center",
        )
        self.print_error_label.pack(pady=(20, 0))

        btn_frame = tk.Frame(self.container, bg=BG)
        btn_frame.pack(pady=30)
        self._big_button(
            btn_frame, "IMPRIMIR", self._on_print, bg=OK,
        ).grid(row=0, column=0, padx=15, ipadx=20, ipady=10)
        self._big_button(
            btn_frame, "Cancelar", self._build_home, bg=BG_PANEL, fg=FG,
        ).grid(row=0, column=1, padx=15, ipadx=20, ipady=10)

    def _on_print(self) -> None:
        data = self.current_label
        assert data is not None
        total = self._qty_var.get()
        try:
            zpl = build_batch_zpl(data, total)
            send_zpl(zpl)
        except PrinterError as exc:
            self.print_error_label.config(text=str(exc))
            return
        self._build_done(total)

    # ---------- pantalla 4: confirmacion ----------
    def _build_done(self, total: int) -> None:
        self._clear()
        label = "etiqueta" if total == 1 else "etiquetas"
        tk.Label(
            self.container, text="✓", font=("Segoe UI", 70, "bold"), bg=BG, fg=OK,
        ).pack(pady=(100, 10))
        tk.Label(
            self.container, text=f"{total} {label} enviada{'s' if total != 1 else ''} a la impresora",
            font=self.font_title, bg=BG, fg=FG, wraplength=800, justify="center",
        ).pack(pady=10)
        self.after(2200, self._build_home)


if __name__ == "__main__":
    App().mainloop()
