"""
SafeSleep - Serviço de logging MQTT para CSV.

Este serviço assina os tópicos de telemetria e alertas do SafeSleep
e grava os dados em arquivos CSV dentro do diretório ``data/``.

Arquitetura:
    SafeSleep Simulador  -->  Broker Mosquitto  -->  Logger (CSV)
                                                \->  MQTTX / Blynk

Arquivos gerados:
    - data/telemetry.csv
    - data/alerts.csv
"""

from __future__ import annotations

import csv
import json
import threading
import time
from pathlib import Path
from typing import Dict, Iterable

import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
KEEPALIVE = 60
CLIENT_ID = "safesleep-logger-01"
QOS = 0

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TELEMETRY_FILE = DATA_DIR / "telemetry.csv"
ALERTS_FILE = DATA_DIR / "alerts.csv"

TELEMETRY_TOPIC = "safesleep/sensors/all"
ALERTS_TOPIC = "safesleep/alerts"

_lock = threading.Lock()


def ensure_data_dir() -> None:
    """Garante que o diretório data/ exista."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def write_csv_row(path: Path, fieldnames: Iterable[str], row: Dict[str, object]) -> None:
    """
    Adiciona uma linha ao arquivo CSV informado.

    Se o arquivo ainda não existir, escreve o cabeçalho primeiro.
    """
    with _lock:
        file_exists = path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)


def handle_telemetry(_: mqtt.Client, __, msg: mqtt.MQTTMessage) -> None:
    """Processa mensagens do tópico de telemetria agregada."""
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        return

    row = {
        "logged_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ts": data.get("ts"),
        "device_id": data.get("device_id"),
        "temperature_c": data.get("temperature_c"),
        "humidity_percent": data.get("humidity_percent"),
        "noise_db": data.get("noise_db"),
        "position": data.get("position"),
    }
    write_csv_row(TELEMETRY_FILE, row.keys(), row)
    print(f"[logger] Telemetria registrada ts={row['ts']} pos={row['position']}")


def handle_alerts(_: mqtt.Client, __, msg: mqtt.MQTTMessage) -> None:
    """Processa mensagens do tópico de alertas."""
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        return

    alerts = data.get("alerts", [])
    if not isinstance(alerts, list):
        alerts = [str(alerts)]

    row = {
        "logged_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ts": data.get("ts"),
        "device_id": data.get("device_id"),
        "alerts": " | ".join(alerts),
    }
    write_csv_row(ALERTS_FILE, row.keys(), row)
    print(f"[logger] ALERTAS registrados ts={row['ts']} qtd={len(alerts)}")


# CORREÇÃO AQUI: Adicionado 'properties=None' para compatibilidade com Paho MQTT v2
def on_connect(client: mqtt.Client, userdata, flags, rc, properties=None) -> None:
    """Assina os tópicos assim que conectar ao broker."""
    if rc != 0:
        print(f"[logger] Falha ao conectar ao broker rc={rc}")
        return
    client.subscribe([(TELEMETRY_TOPIC, QOS), (ALERTS_TOPIC, QOS)])
    print(
        f"[logger] Conectado. Assinado {TELEMETRY_TOPIC} e {ALERTS_TOPIC}"
    )


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    """Despacha mensagens para o handler apropriado."""
    if msg.topic == TELEMETRY_TOPIC:
        handle_telemetry(client, userdata, msg)
    elif msg.topic == ALERTS_TOPIC:
        handle_alerts(client, userdata, msg)


def run() -> None:
    """Inicializa o logger e bloqueia até interrupção (Ctrl+C)."""
    ensure_data_dir()

    # CORREÇÃO AQUI: Definindo explicitamente a versão da API como V2
    client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[logger] Conectando ao broker {BROKER_HOST}:{BROKER_PORT} ...")
    client.connect(BROKER_HOST, BROKER_PORT, KEEPALIVE)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[logger] Encerrando logger ...")


if __name__ == "__main__":
    run()