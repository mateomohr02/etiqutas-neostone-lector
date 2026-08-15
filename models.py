"""Formato del código QR de las etiquetas Neostone.

Payload compacto separado por "|" (en vez de JSON) para mantener el QR
chico y confiable de escanear a la distancia/calidad de una pistola USB.
Orden fijo, sin nombres de campo dentro del string.
"""
from __future__ import annotations

from dataclasses import dataclass

QR_VERSION = "NEO1"
_FIELD_COUNT = 11  # version + 10 campos de datos


class InvalidLabelQR(ValueError):
    pass


@dataclass
class LabelData:
    pedido: str
    id_escena: str
    cliente: str
    poblacion: str
    descripcion: str
    medida_l: str
    medida_h: str
    medida_p: str
    bulto: int
    total_bultos: int

    @classmethod
    def from_qr(cls, raw: str) -> "LabelData":
        parts = raw.strip().split("|")
        if len(parts) != _FIELD_COUNT or parts[0] != QR_VERSION:
            raise InvalidLabelQR(f"Código QR no reconocido: {raw!r}")
        (_, pedido, id_escena, cliente, poblacion, descripcion,
         l, h, p, bulto, total) = parts
        try:
            bulto_i = int(bulto)
            total_i = int(total)
        except ValueError as exc:
            raise InvalidLabelQR(f"Contador de bultos inválido en QR: {raw!r}") from exc
        return cls(pedido, id_escena, cliente, poblacion, descripcion,
                   l, h, p, bulto_i, total_i)

    def to_qr(self) -> str:
        return "|".join([
            QR_VERSION, self.pedido, self.id_escena, self.cliente, self.poblacion,
            self.descripcion, self.medida_l, self.medida_h, self.medida_p,
            str(self.bulto), str(self.total_bultos),
        ])

    def with_bulto(self, bulto: int, total_bultos: int) -> "LabelData":
        return LabelData(
            pedido=self.pedido, id_escena=self.id_escena, cliente=self.cliente,
            poblacion=self.poblacion, descripcion=self.descripcion,
            medida_l=self.medida_l, medida_h=self.medida_h, medida_p=self.medida_p,
            bulto=bulto, total_bultos=total_bultos,
        )
