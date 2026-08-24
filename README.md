# Lector de Etiquetas Neostone

App de escritorio para reimprimir etiquetas Zebra ZD220t en múltiples bultos.

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

El QR debe contener los campos separados por TAB (`\t`):
```
NEO1<TAB>pedido<TAB>id_escena<TAB>cliente<TAB>poblacion<TAB>descripcion<TAB>medida_L<TAB>medida_H<TAB>medida_P<TAB>bulto<TAB>total_bultos
```

Ejemplo (mostrando el TAB como `|` solo para legibilidad, en el QR real es un carácter de tabulación):
```
NEO1|S1-00498|18|ARQ. MEICHTRY CAROLINA|SALTA|AJUSTE PARA COLUMNAS|100,00|2040,00|18,00|1|1
```

> El separador es TAB y no `|`: la pistola lectora (emulación de teclado/HID) no
> transmite `|` de forma confiable sin importar el layout de teclado configurado,
> mientras que TAB es una tecla directa sin combinaciones. Etiquetas viejas
> separadas por `|` se siguen aceptando como fallback (ver `models.py`).

## Flujo de uso

1. **Pantalla de inicio**: Clic en "ESCANEAR ETIQUETA"
2. **Escaneo**: Apuntá la pistola lectora a la etiqueta original
3. **Cantidad**: Indicá en cuántos bultos se separó el módulo (+/-)
4. **Impresión**: Clic en "IMPRIMIR" → se envían las N etiquetas a la Zebra
5. **Confirmación**: La app regresa al inicio automáticamente

## Especificaciones de impresión

- **Impresora**: Zebra ZD220t (USB), configurada como predeterminada en Windows
- **Tamaño etiqueta**: 9,80 × 5,90 cm
- **Velocidad**: 12,7 cm/s
- **Oscuridad**: 15 (`^MD`, ajustable en `zpl_builder.py`, escala 0-30)
- **Márgenes no imprimibles**: 0,40 cm
- **QR**: magnificación dinámica (hasta x4) según la cantidad de contenido, para no exceder el recuadro reservado

## Archivos del proyecto

- `app.py` — Interfaz gráfica (Tkinter)
- `models.py` — Definición del formato QR
- `zpl_builder.py` — Generador de ZPL para Zebra
- `printer.py` — Comunicación con la impresora USB
- `requirements.txt` — Dependencias (pywin32, qrcode)
- `run.bat` — Ejecutable rápido
- `neostone.log` — Log de escaneos, impresiones y parámetros del QR generado (se crea al ejecutar la app)
- `ultima_etiqueta.zpl` — ZPL crudo del último trabajo de impresión (se sobreescribe en cada impresión)

## Notas para desarrollo

Si necesitás ajustar las coordenadas del layout de la etiqueta:
1. Abrí `zpl_builder.py`
2. Modificá las constantes `*_DOTS` al principio del archivo
3. Guardá y corrí `run.bat` nuevamente

Los valores están en "dots" (puntos de impresión a 203 dpi, ~8 dots/mm).
