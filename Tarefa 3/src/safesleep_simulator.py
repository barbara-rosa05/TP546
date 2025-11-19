"""
SafeSleep - Simulador de monitoramento de bebê via MQTT.

Este script representa um dispositivo IoT instalado próximo ao berço
do bebê. Ele gera leituras simuladas de:

- Temperatura do quarto (°C)
- Umidade relativa do ar (%)
- Nível de ruído (dB) – proxy para choro/barulho
- Posição do bebê (supino, lateral, prono)

As leituras são publicadas em tópicos MQTT específicos e também em um
tópico agregado em formato JSON. Regras simples são aplicadas para
detectar situações de risco ou desconforto, gerando mensagens de alerta.
"""

from __future__ import annotations

import json
import random
import time
from typing import Dict, List

import paho.mqtt.client as mqtt

# ==============================
# Configurações MQTT
# ==============================

BROKER_HOST = "localhost"   # broker local (Mosquitto)
BROKER_PORT = 1883
KEEPALIVE = 60
CLIENT_ID = "safesleep-simulator-01"
QOS = 0

# Tópicos
TOPIC_TEMPERATURE = "safesleep/sensors/temperature"
TOPIC_HUMIDITY = "safesleep/sensors/humidity"
TOPIC_NOISE = "safesleep/sensors/noise"
TOPIC_POSITION = "safesleep/sensors/position"
TOPIC_ALL = "safesleep/sensors/all"      # JSON com todos os campos
TOPIC_ALERTS = "safesleep/alerts"        # JSON com lista de alertas

PUBLISH_INTERVAL_SECONDS = 3  # intervalo entre leituras


# ==============================
# Callbacks MQTT
# ==============================

# CORREÇÃO AQUI: Adicionado 'properties=None' para compatibilidade com Paho MQTT v2
def on_connect(client: mqtt.Client, userdata, flags, rc, properties=None) -> None:
    """Chamado quando conecta ao broker."""
    if rc == 0:
        print(f"[MQTT] Conectado ao broker {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"[MQTT] Falha na conexão. Código rc={rc}")


def on_disconnect(client: mqtt.Client, userdata, rc, properties=None) -> None:
    """Chamado quando desconecta do broker."""
    print(f"[MQTT] Desconectado do broker rc={rc}")


# ==============================
# Simulação de sensores
# ==============================


def simulate_sensors() -> Dict[str, object]:
    """
    Gera leituras fictícias para todos os sensores do SafeSleep.
    """
    temperature_c = round(random.uniform(18.0, 30.0), 1)
    humidity_percent = round(random.uniform(30.0, 70.0), 1)
    noise_db = round(random.uniform(20.0, 90.0), 1)

    position = random.choices(
        population=["supino", "lateral", "prono"],
        weights=[0.6, 0.25, 0.15],
        k=1,
    )[0]

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return {
        "ts": timestamp,
        "device_id": "safesleep-dev-01",
        "temperature_c": temperature_c,
        "humidity_percent": humidity_percent,
        "noise_db": noise_db,
        "position": position,
    }


def evaluate_alerts(data: Dict[str, object]) -> List[str]:
    """
    Aplica regras simples de segurança / conforto.
    """
    alerts: List[str] = []

    temp = float(data["temperature_c"])
    hum = float(data["humidity_percent"])
    noise = float(data["noise_db"])
    pos = str(data["position"])

    if temp < 20.0:
        alerts.append("Temperatura abaixo do recomendado para o bebê (< 20 ºC).")
    elif temp > 26.0:
        alerts.append("Temperatura acima do recomendado para o bebê (> 26 ºC).")

    if hum < 40.0:
        alerts.append("Umidade baixa – ambiente mais seco que o ideal (< 40%).")
    elif hum > 60.0:
        alerts.append("Umidade alta – risco de mofo/desconforto (> 60%).")

    if noise > 60.0:
        alerts.append("Nível de ruído elevado – possível choro ou barulho no quarto (> 60 dB).")

    if pos == "prono":
        alerts.append("Bebê em posição de bruços (prono) – atenção ao risco de sufocamento.")

    return alerts


# ==============================
# Main
# ==============================


def main() -> None:
    """Loop principal do simulador SafeSleep."""
    # CORREÇÃO AQUI: Definindo explicitamente a versão da API como V2
    client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    print(f"[SafeSleep] Conectando ao broker MQTT {BROKER_HOST}:{BROKER_PORT} ...")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, KEEPALIVE)
    except ConnectionRefusedError:
        print(f"[ERRO] Não foi possível conectar em {BROKER_HOST}:{BROKER_PORT}.")
        print("Verifique se o Mosquitto está rodando.")
        return

    # Loop de rede em background
    client.loop_start()

    try:
        while True:
            sensor_data = simulate_sensors()
            alerts = evaluate_alerts(sensor_data)

            # Publica valores individuais (opcional, bom para debug)
            client.publish(TOPIC_TEMPERATURE, sensor_data["temperature_c"], qos=QOS)
            client.publish(TOPIC_HUMIDITY, sensor_data["humidity_percent"], qos=QOS)
            client.publish(TOPIC_NOISE, sensor_data["noise_db"], qos=QOS)
            position_payload = json.dumps(
                {"position": sensor_data["position"]},
                ensure_ascii=False,
            )
            client.publish(TOPIC_POSITION, position_payload, qos=QOS)


            # Publica pacote completo em JSON (ISSO O LOGGER LÊ)
            payload_all = json.dumps(sensor_data, ensure_ascii=False)
            client.publish(TOPIC_ALL, payload_all, qos=QOS)

            print("\n[SafeSleep] Telemetria enviada:")
            print(f"  ts          : {sensor_data['ts']}")
            print(f"  temp        : {sensor_data['temperature_c']} ºC")
            print(f"  umidade     : {sensor_data['humidity_percent']} %")
            print(f"  ruído       : {sensor_data['noise_db']} dB")
            print(f"  posição     : {sensor_data['position']}")

            # Publica alertas (ISSO O LOGGER LÊ)
            if alerts:
                alert_payload = json.dumps(
                    {
                        "ts": sensor_data["ts"],
                        "device_id": sensor_data["device_id"],
                        "alerts": alerts,
                    },
                    ensure_ascii=False,
                )
                client.publish(TOPIC_ALERTS, alert_payload, qos=QOS)
                print("[SafeSleep] ALERTAS:")
                for a in alerts:
                    print(f"  - {a}")
            else:
                print("[SafeSleep] Nenhum alerta gerado.")

            time.sleep(PUBLISH_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[SafeSleep] Encerrando simulador ...")

    finally:
        client.loop_stop()
        client.disconnect()
        print("[SafeSleep] Desconectado do broker.")


if __name__ == "__main__":
    main()