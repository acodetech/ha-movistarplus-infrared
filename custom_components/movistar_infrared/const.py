"""Constants and helpers for Movistar+ Infrared integration."""

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
import re
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from infrared_protocols.commands import Command

DOMAIN: Final = "movistar_infrared"
CONF_INFRARED_EMITTER_ENTITY_ID: Final = "infrared_emitter_entity_id"
CONF_REPEAT_COUNT: Final = "repeat_count"
CONF_DIGIT_DELAY_MS: Final = "digit_delay_ms"

DEFAULT_NAME: Final = "Movistar+ Descodificador"
DEFAULT_REPEAT_COUNT: Final = 3
DEFAULT_DIGIT_DELAY_MS: Final = 350


def get_entry_settings(entry: ConfigEntry) -> tuple[str, int, int]:
    """Return (emitter_entity_id, repeat_count, digit_delay_ms) from options or data."""
    emitter_entity_id = entry.options.get(
        CONF_INFRARED_EMITTER_ENTITY_ID,
        entry.data[CONF_INFRARED_EMITTER_ENTITY_ID],
    )
    repeat_count = int(entry.options.get(CONF_REPEAT_COUNT, DEFAULT_REPEAT_COUNT))
    digit_delay_ms = int(entry.options.get(CONF_DIGIT_DELAY_MS, DEFAULT_DIGIT_DELAY_MS))
    return emitter_entity_id, repeat_count, digit_delay_ms


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Build consistent DeviceInfo for all Movistar+ Infrared entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title or DEFAULT_NAME,
        manufacturer="Movistar",
        model="Descodificador UHD / IPTV",
    )


def expand_digit_commands(value: str) -> list[str] | None:
    """Expand a dial number or channel label (e.g. '69' or '69 - DAZN F1') into num_* keys."""
    match = re.match(r"^(\d+)(?:\s*-.*)?$", value.strip())
    if not match:
        return None
    return [f"num_{digit}" for digit in match.group(1)]


class ProntoCommand(Command):
    """Command that converts Pronto Hex to carrier frequency and microsecond pulse/space timings."""

    def __init__(self, pronto_hex: str, repeat_count: int = DEFAULT_REPEAT_COUNT) -> None:
        parts = [int(p, 16) for p in pronto_hex.strip().split()]
        if not parts or parts[0] != 0:
            raise ValueError("Invalid Pronto Hex code")

        freq = round(4145146 / parts[1])
        super().__init__(modulation=freq, repeat_count=repeat_count)

        us_per_cycle = 1000000.0 / freq
        # Some Pronto hex exports (like Movistar+.irplus) have a header indicating 16 pairs
        # but contain 17 pairs in the payload. Parse all available pairs so the final pulse/space isn't truncated.
        total_pairs = (len(parts) - 4) // 2
        single_burst: list[int] = []
        idx = 4
        for _ in range(total_pairs):
            if idx + 1 >= len(parts):
                break
            pulse = round(parts[idx] * us_per_cycle)
            space = round(parts[idx + 1] * us_per_cycle)
            single_burst.append(pulse)
            single_burst.append(-space)
            idx += 2

        # Repeat burst (default 3 times, matching Movistar+ protocol requirement and original Zigbee blaster)
        timings: list[int] = []
        for _ in range(max(1, repeat_count)):
            timings.extend(single_burst)

        self._timings = timings

    def get_raw_timings(self) -> list[int]:
        """Return pulse (>0) and space (<0) durations in microseconds."""
        return self._timings


@dataclass(frozen=True, kw_only=True)
class MovistarButtonDef:
    key: str
    name: str
    icon: str
    code: str


MOVISTAR_BUTTONS: list[MovistarButtonDef] = [
    MovistarButtonDef(key="power_toggle", name="Encender / Apagar", icon="mdi:power", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0024 0012 005a 0012 0024 0012 0024 0012 0036 0012 006c 0012 0024 0012 0C32"),
    MovistarButtonDef(key="power", name="Power", icon="mdi:power", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 005A 0012 0012 0012 0036 0012 0036 0012 005A 0012 0024 0012 0C32"),
    MovistarButtonDef(key="red", name="Rojo", icon="mdi:circle", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0024 0012 005A 0012 0048 0026 0036 0012 0036 0012 0036 0012 0C32"),
    MovistarButtonDef(key="green", name="Verde", icon="mdi:circle", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 006c 0012 0036 0012 0036 0024 0036 0012 0036 0012 006c 0012 0C32"),
    MovistarButtonDef(key="yellow", name="Amarillo", icon="mdi:circle", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 005a 0012 0024 0012 0012 0012 0036 0012 0036 0012 0036 0012 0036 0012 0C32"),
    MovistarButtonDef(key="blue", name="Azul", icon="mdi:circle", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 005A 0012 0036 0026 0036 0012 0036 0012 0048 0012 0C32"),
    MovistarButtonDef(key="info", name="Buscar", icon="mdi:magnify", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 005A 0012 0036 0012 0048 0026 0036 0012 006C 0012 0024 0012 0C32"),
    MovistarButtonDef(key="guide", name="Guía", icon="mdi:television-guide", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0048 0012 0036 0012 0036 0012 0012 0012 0036 0012 0036 0012 0048 0012 0C32"),
    MovistarButtonDef(key="help", name="Ayuda", icon="mdi:help-circle-outline", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 005a 0012 0036 0024 0036 0012 0036 0012 0048 0012 0024 0012 0C32"),
    MovistarButtonDef(key="volume_up", name="Volumen +", icon="mdi:volume-plus", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0024 0012 006C 0012 0012 0012 0024 0012 0036 0012 0036 0012 005A 0012 0C32"),
    MovistarButtonDef(key="nav_up", name="Arriba", icon="mdi:chevron-up", code="0000 0048 0000 0020 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 006C 0012 0024 0012 0012 0012 0036 0012 0036 0012 006C 0026 0C56"),
    MovistarButtonDef(key="channel_up", name="Canal +", icon="mdi:menu-up", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 006c 0012 0024 0012 0024 0012 0024 0012 0036 0012 006c 0012 0012 0012 0C32"),
    MovistarButtonDef(key="nav_left", name="Izquierda", icon="mdi:chevron-left", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0036 0012 0048 0012 0012 0012 0036 0012 0036 0012 006c 0012 0024 0012 0C32"),
    MovistarButtonDef(key="ok", name="OK", icon="mdi:checkbox-marked-circle-outline", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 006c 0012 0036 0024 0036 0012 0036 0012 0036 0012 0C32"),
    MovistarButtonDef(key="nav_right", name="Derecha", icon="mdi:chevron-right", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0048 0012 0036 0012 0012 0012 0036 0012 0036 0012 006c 0012 0036 0012 0C32"),
    MovistarButtonDef(key="volume_down", name="Volumen -", icon="mdi:volume-minus", code="0000 0048 0000 0022 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 006C 0012 0036 0012 0012 0012 0024 0012 0036 0012 0036 0012 0048 0012 0C32"),
    MovistarButtonDef(key="nav_down", name="Abajo", icon="mdi:chevron-down", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0024 0012 005a 0012 0012 0012 0036 0012 0036 0012 006d 0012 0012 0012 0C32"),
    MovistarButtonDef(key="channel_down", name="Canal -", icon="mdi:menu-down", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 005a 0012 0036 0012 0024 0012 0012 0012 0036 0012 0048 0012 0048 0012 0C32"),
    MovistarButtonDef(key="back", name="Atrás", icon="mdi:arrow-left", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0036 0012 0048 0012 0048 0024 0036 0012 0036 0012 0048 0012 0C32"),
    MovistarButtonDef(key="menu", name="Menú", icon="mdi:menu", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 005a 0012 0048 0012 0036 0024 0036 0012 0036 0012 005a 0012 0C32"),
    MovistarButtonDef(key="favorite", name="Favoritos", icon="mdi:star", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0048 0012 0024 0012 0024 0012 0036 0012 005a 0012 0048 0012 0C32"),
    MovistarButtonDef(key="num_1", name="1", icon="mdi:numeric-1", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0036 0012 0048 0012 0024 0012 0024 0012 0036 0012 006c 0012 0036 0012 0C32"),
    MovistarButtonDef(key="num_2", name="2", icon="mdi:numeric-2", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0048 0012 0036 0012 0024 0012 0024 0012 0036 0012 0036 0012 0036 0012 0C32"),
    MovistarButtonDef(key="num_3", name="3", icon="mdi:numeric-3", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 005a 0012 0024 0012 0024 0012 0024 0012 0036 0012 0036 0012 0048 0012 0C32"),
    MovistarButtonDef(key="num_4", name="4", icon="mdi:numeric-4", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 005A 0026 0036 0012 0036 0012 006C 0012 0024 0012 0C32"),
    MovistarButtonDef(key="num_5", name="5", icon="mdi:numeric-5", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 005a 0012 0048 0024 0036 0012 0036 0012 006c 0012 0036 0012 0C32"),
    MovistarButtonDef(key="num_6", name="6", icon="mdi:numeric-6", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 006c 0012 0036 0024 0036 0012 0036 0012 0036 0012 0036 0012 0C32"),
    MovistarButtonDef(key="num_7", name="7", icon="mdi:numeric-7", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0024 0012 006c 0024 0036 0012 0036 0012 0036 0012 0048 0012 0C32"),
    MovistarButtonDef(key="num_8", name="8", icon="mdi:numeric-8", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0036 0012 005a 0024 0036 0012 0036 0012 0036 0012 005a 0012 0C32"),
    MovistarButtonDef(key="num_9", name="9", icon="mdi:numeric-9", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0048 0012 0048 0024 0036 0012 0036 0012 0036 0012 006c 0012 0C32"),
    MovistarButtonDef(key="mute", name="Silencio", icon="mdi:volume-off", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0048 0012 0036 0012 0048 0026 0036 0012 0036 0012 005A 0012 0C32"),
    MovistarButtonDef(key="num_0", name="0", icon="mdi:numeric-0", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 005a 0012 0012 0012 0024 0012 0036 0012 006c 0012 0036 0012 0C32"),
    MovistarButtonDef(key="subtitles", name="Subtítulos", icon="mdi:subtitles", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0036 0012 005a 0012 0012 0012 0024 0012 0036 0012 0036 0012 006c 0012 0C32"),
    MovistarButtonDef(key="rewind", name="Rebobinar", icon="mdi:rewind", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 005a 0012 0036 0012 0036 0012 0012 0012 0036 0012 006c 0012 0012 0012 0C32"),
    MovistarButtonDef(key="fast_forward", name="Avance Rápido", icon="mdi:fast-forward", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 005a 0012 0036 0012 0024 0012 0024 0012 0036 0012 006c 0024 126b"),
    MovistarButtonDef(key="step_back", name="Salto Atrás", icon="mdi:skip-backward", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 006c 0012 0024 0012 0036 0012 0012 0012 0036 0012 006c 0012 0024 0012 0C32"),
    MovistarButtonDef(key="step_forward", name="Salto Adelante", icon="mdi:skip-forward", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0048 0012 0024 0012 005a 0012 0036 0012 0012 0012 0036 0012 006c 0012 0036 0012 0C32"),
    MovistarButtonDef(key="play_pause", name="Play / Pausa", icon="mdi:play-pause", code="0000 0048 0000 0010 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 005a 0012 0036 0012 0012 0012 0036 0012 005a 0012 0048 0012 0C32"),
    MovistarButtonDef(key="record", name="Grabar", icon="mdi:record-rec", code="0000 0048 0000 0011 0036 0036 0024 0048 0012 0024 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 0036 0012 005A 0012 0012 0012 0048 0012 0024 0012 0036 0012 0048 0012 0024 0012 0C32"),
]

MOVISTAR_CODE_MAP: dict[str, str] = {b.key: b.code for b in MOVISTAR_BUTTONS}


async def async_send_key_sequence(
    send_fn: Callable[[Command], Awaitable[None]],
    keys: Iterable[str],
    repeat_count: int,
    delay_secs: float,
) -> None:
    """Send a sequence of Movistar+ button keys via the configured IR emitter."""
    first = True
    for key in keys:
        code = MOVISTAR_CODE_MAP.get(key)
        if not code:
            continue
        if not first and delay_secs > 0:
            await asyncio.sleep(delay_secs)
        first = False
        await send_fn(ProntoCommand(code, repeat_count=repeat_count))

MOVISTAR_CHANNELS: tuple[str, ...] = (
    "0 - Portada",
    "1 - La 1",
    "2 - La 2",
    "3 - Antena 3",
    "4 - Cuatro",
    "5 - Telecinco",
    "6 - La Sexta",
    "7 - #Movistar Plus+",
    "8 - #Vamos",
    "9 - TV3 / Autonómico 1",
    "10 - 33 / Esport3 / Autonómico 2",
    "12 - Estrenos por M+",
    "13 - Hits por M+",
    "14 - Originales por M+",
    "15 - Pop Up por M+",
    "17 - Documentales por M+",
    "18 - Terror por M+",
    "20 - Clásicos por M+",
    "21 - Acción por M+",
    "22 - Comedia por M+",
    "23 - Drama por M+",
    "24 - Indie por M+",
    "25 - Cine Español por M+",
    "26 - HBO Max Avances (Solo fibra / ADSL)",
    "27 - SkyShowtime 1",
    "28 - Flixolé 1 (Solo fibra / ADSL)",
    "29 - Flixolé 2 (Solo fibra / ADSL)",
    "30 - TCM",
    "31 - AXN Movies",
    "32 - BBC Series",
    "34 - BBC Top Gear",
    "36 - BeMad",
    "37 - Star Channel",
    "38 - AXN",
    "39 - Warner TV",
    "40 - Comedy Central",
    "41 - Calle 13",
    "42 - Cosmo",
    "43 - Syfy",
    "44 - Veo7",
    "45 - Trece",
    "46 - Energy",
    "47 - FDF",
    "48 - Neox",
    "49 - Atreseries",
    "50 - Vamos por M+",
    "51 - Vamos 2 por M+",
    "52 - Primera Federación",
    "54 - LaLiga por M+",
    "55 - DAZN LaLiga",
    "56 - LaLiga TV Hypermotion",
    "57 - LaLiga 2 por M+",
    "58 - DAZN La Liga 2",
    "59 - LaLiga TV Hypermotion 2",
    "60 - Liga de Campeones por M+",
    "61 - Liga de Campeones 2 por M+",
    "62 - Liga de Campeones 3 por M+",
    "63 - Deportes por M+",
    "64 - Deportes 2 por M+",
    "65 - Deportes 3 por M+",
    "66 - Ellas Vamos por M+",
    "67 - Golf por M+",
    "68 - Golf 2 por M+",
    "69 - DAZN F1",
    "70 - DAZN 1",
    "71 - DAZN 2",
    "72 - Eurosport 1",
    "73 - Eurosport 2",
    "74 - GOL",
    "75 - Teledeporte",
    "76 - Real Madrid TV",
    "77 - Caza y Pesca TV",
    "78 - Iberalia TV",
    "79 - El Garage TV",
    "81 - UBEAT",
    "82 - National Geographic",
    "83 - Nat Geo Wild",
    "84 - BBC History",
    "85 - Discovery",
    "86 - BBC Earth",
    "87 - DAZN Baloncesto",
    "88 - DAZN Baloncesto 2",
    "89 - DMAX",
    "90 - DAZN Baloncesto 3",
    "92 - BBC Food",
    "93 - BBC Lifestyle",
    "94 - DKiss",
    "95 - Divinity",
    "96 - Nova",
    "97 - Mega",
    "98 - Ten",
    "110 - BabyTV",
    "111 - Disney Junior",
    "113 - Nick Jr",
    "114 - Nickelodeon",
    "115 - DreamWorks",
    "117 - Boing",
    "118 - Clan TVE",
    "119 - ETB3 (solo en el País Vasco – solo fibra)",
    "120 - MTV España",
    "123 - Mezzo",
    "124 - Mezzo Live HD",
    "125 - Stingray Classica",
    "127 - Canal 24 H.",
    "128 - BBC World",
    "129 - CNN Int.",
    "131 - Euronews",
    "132 - Al Jazeera English",
    "133 - France 24 (FR)",
    "134 - 3CatInfo (Solo fibra / ADSL)",
    "135 - 1 + 1 International",
    "136 - CNBC Eur.",
    "137 - TV5 Monde",
    "138 - Bloomberg",
    "139 - Sky News (Solo Satélite)",
    "140 - Negocios TV",
    "141 - CGTN Español",
    "142 - CGTN Documentary HD",
    "143 - UCL",
    "144 - Canal de las Estrellas (Solo Fibra)",
    "145 - Arirang TV HD (Solo Satélite)",
    "146 - TV Colombia (Solo fibra / ADSL)",
    "147 - Cubavisión",
    "148 - TeleSUR",
    "149 - EWTN (Solo Fibra / ADSL)",
    "151 - Canal Sur Andalucía",
    "152 - TVG Europa",
    "153 - Canal Extremadura SAT",
    "154 - TV3CAT",
    "155 - ETB Basque",
    "156 - Aragón TV Int.",
    "157 - Telemadrid Int",
    "164 - Esport 3 (Solo fibra / ADSL)",
    "166 - Betevé (Solo fibra / ADSL)",
    "167 - LaLiga 3 por M+",
    "168 - LaLiga 4 por M+",
    "169 - LaLiga 5 por M+",
    "170 - M+ Liga de Campeones 14",
    "171 - M+ Liga de Campeones 15",
    "172 - M+ Liga de Campeones 16",
    "173 - M+ Liga de Campeones 17",
    "174 - M+ Liga de Campeones 18",
    "175 - M+ Liga de Campeones 19",
    "178 - LaLiga TV Hypermotion 3",
    "180 - M+ Liga de Campeones 4",
    "181 - M+ Liga de Campeones 5",
    "182 - M+ Liga de Campeones 6",
    "183 - M+ Liga de Campeones 7",
    "184 - M+ Liga de Campeones 8",
    "185 - M+ Liga de Campeones 9",
    "186 - M+ Liga de Campeones 10",
    "187 - M+ Liga de Campeones 11",
    "188 - M+ Liga de Campeones 12",
    "189 - M+ Liga de Campeones 13",
    "191 - M+ Deportes 4",
    "192 - M+ Deportes 5",
    "193 - M+ Deportes 6",
    "194 - M+ Deportes 7",
    "196 - DAZN 3",
    "197 - DAZN 4",
    "198 - Alquiler 1 (Solo Satélite)",
    "199 - Canal Fútbol Replay (Solo fibra)",
    "222 - FLASH Fútbol",
    "440 - LaLiga HDR por M+",
    "441 - LaLiga 2 HDR por M+",
    "444 - Wimbledon UHD por M+ (desco UHD)",
    "450 - LaLiga 3 por M+",
)
