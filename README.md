# Lector de Etiquetas Neostone

App de escritorio para reimprimir etiquetas Zebra GK420t en múltiples bultos.

## Instalación

✓ Ya está lista. Solo necesitás ejecutar la app.

## Ejecución

### Opción 1: Doble clic (recomendado)
Doble clic en `run.bat`

### Opción 2: Terminal
```bash
python app.py
```

## Formato del QR

El QR debe contener:
```
NEO1|pedido|id_escena|cliente|poblacion|descripcion|medida_L|medida_H|medida_P|bulto|total_bultos
```

Ejemplo:
```
NEO1|S1-00498|18|ARQ. MEICHTRY CAROLINA|SALTA|AJUSTE PARA COLUMNAS|100,00|2040,00|18,00|1|1
```

## Flujo de uso

1. **Pantalla de inicio**: Clic en "ESCANEAR ETIQUETA"
2. **Escaneo**: Apuntá la pistola lectora a la etiqueta original
3. **Cantidad**: Indicá en cuántos bultos se separó el módulo (+/-)
4. **Impresión**: Clic en "IMPRIMIR" → se envían las N etiquetas a la Zebra
5. **Confirmación**: La app regresa al inicio automáticamente

## Especificaciones de impresión

- **Impresora**: Zebra GK420t (USB)
- **Tamaño etiqueta**: 10,80 × 7,00 cm
- **Velocidad**: 12,7 cm/s
- **Oscuridad**: 1
- **Márgenes no imprimibles**: 0,20 cm (izq/der)

## Archivos del proyecto

- `app.py` — Interfaz gráfica (Tkinter)
- `models.py` — Definición del formato QR
- `zpl_builder.py` — Generador de ZPL para Zebra
- `printer.py` — Comunicación con la impresora USB
- `requirements.txt` — Dependencias (pywin32)
- `run.bat` — Ejecutable rápido

## Notas para desarrollo

Si necesitás ajustar las coordenadas del layout de la etiqueta:
1. Abrí `zpl_builder.py`
2. Modificá las constantes `*_DOTS` al principio del archivo
3. Guardá y corrí `run.bat` nuevamente

Los valores están en "dots" (puntos de impresión a 203 dpi, ~8 dots/mm).
