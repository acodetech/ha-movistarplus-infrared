# Movistar+ Infrared Integration for Home Assistant

[![HA Marketplace](https://img.shields.io/badge/Home%20Assistant-Marketplace-03A9F4.svg)](https://github.com/acodetech/ha-movistarplus-infrared)
[![GitHub release](https://img.shields.io/github/v/release/acodetech/ha-movistarplus-infrared)](https://github.com/acodetech/ha-movistarplus-infrared/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Integración personalizada para **Home Assistant** que permite controlar de forma nativa e instantánea los decodificadores de **Movistar+** (modelos UHD / 4K y HD de Arris y Humax) a través de cualquier transmisor infrarrojo compatible con la plataforma nativa `infrared` de Home Assistant (como emisores **ESPHome**, Tuya WiFi flasheados o proxies IR).

---

## ⚡ Características principales

- **Integración nativa con la plataforma `infrared`**: Se apoya en la arquitectura de Home Assistant (HA 2026.4+), delegando la transmisión al hardware del emisor con latencia casi nula (<50ms).
- **Selector nativo de canales (`select.*_canal`)**: Incluye el listado completo de canales de Movistar+ (167 diales) para cambiar de canal directamente desde el dashboard sin necesidad de crear `input_select`, scripts ni automatizaciones manuales.
- **Entidad `remote` mejorada (`remote.*_mando`)**: Soporta encendido/apagado, botones sueltos y cambio directo de canal con diales multidígito o etiquetas de canal (por ejemplo `"54"`, `"222"` o `"69 - DAZN F1"`) en `remote.send_command`.
- **40 botones individuales (`button.*`)**: Todos los mandos oficiales mapeados (números 0–9, cruceta, OK, Guía, Menú, Info, colores, reproducción, volumen, etc.).
- **Opciones configurables desde la UI (`Configurar`)**: Permite cambiar el emisor infrarrojo, las repeticiones IR (`1–5`, por defecto `3`) y el retardo entre dígitos (`100–1000 ms`, por defecto `350 ms`) sin eliminar ni recrear entidades.
- **Trama y modulación exactas**: Configurado a la frecuencia de portadora exacta de Movistar (**57.6 kHz**) con ráfagas y espacios calibrados para el receptor del decodificador.

---

## 📦 Instalación

### Opción 1: A través del Marketplace de Home Assistant (Recomendado, HA 2026.11+)

A partir de Home Assistant 2026.11, **HACS** viene integrado de serie bajo **Ajustes > Marketplace** (en versiones anteriores sigue siendo 100% compatible a través de **HACS** usando los mismos pasos):

1. En Home Assistant, ve a **Ajustes** > **Marketplace** *(o **HACS** en HA 2026.10 o anterior)*.
2. Haz clic en el menú de los 3 puntos (esquina superior derecha) y selecciona **Repositorios personalizados**.
3. Pega la URL de este repositorio:
   `https://github.com/acodetech/ha-movistarplus-infrared`
4. En **Categoría**, selecciona **Integración**.
5. Haz clic en **Añadir**, busca **Movistar+ Infrared** y descárgalo.
6. Configura la integración cuando aparezca el asistente *(o reinicia Home Assistant si tu versión lo solicita)*.

A partir de ese momento, cualquier nueva versión publicada en GitHub aparecerá automáticamente en **Ajustes > Sistema > Actualizaciones**.

### Opción 2: Instalación manual

1. Descarga el archivo zip de la última versión en [Releases](https://github.com/acodetech/ha-movistarplus-infrared/releases).
2. Copia la carpeta `custom_components/movistar_infrared` dentro de la carpeta `/config/custom_components/` de tu Home Assistant.
3. Reinicia Home Assistant.

---

## ⚙️ Configuración

1. En Home Assistant, ve a **Ajustes** > **Dispositivos y servicios**.
2. Pulsa en **Añadir integración** y busca **Movistar+ Infrared**.
3. Selecciona la entidad de tu transmisor infrarrojo (por ejemplo, `infrared.salon` de ESPHome).
4. Asigna un nombre (por ejemplo *Movistar+ Salón*) y guarda.

Se crearán automáticamente bajo el mismo dispositivo:
* 1 entidad `select.*_canal` (selector nativo de canales)
* 1 entidad `remote.*_mando`
* 40 entidades `button.*`

Desde el botón **Configurar** de la integración puedes ajustar en cualquier momento el emisor IR, el número de repeticiones (`repeat_count`) y el retardo entre dígitos (`digit_delay_ms`).

---

## 💡 Ejemplos de uso

### Cambiar de canal mediante `select.select_option`

```yaml
action: select.select_option
target:
  entity_id: select.movistar_descodificador_canal
data:
  option: "69 - DAZN F1"
```

### Cambiar de canal mediante `remote.send_command` (con dial directo o secuencia)

```yaml
action: remote.send_command
target:
  entity_id: remote.movistar_descodificador_mando
data:
  command:
    - "54"
```

También acepta el formato tradicional dígito a dígito o secuencias de teclas (por ejemplo `["2", "4", "ok"]` o `["guide"]`).

### Automatización: Poner DAZN F1 al llegar a casa

```yaml
alias: "Movistar - Poner DAZN F1"
trigger:
  - platform: state
    entity_id: binary_sensor.presencia_salon
    to: "on"
action:
  - action: select.select_option
    target:
      entity_id: select.movistar_descodificador_canal
    data:
      option: "69 - DAZN F1"
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
