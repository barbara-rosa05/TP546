[![Vídeo Explicativo no YouTube](https://img.shields.io/badge/YouTube-Assistir-FF0000?logo=youtube&logoColor=white)](https://youtu.be/ZEI4JqBuyhI)

![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)

# 🍼 SafeSleep — Sistema IoT de Monitoramento de Bebê via MQTT

O **SafeSleep** é um sistema IoT completo para monitoramento de ambiente e postura do bebê utilizando sensores simulados, um broker MQTT (Mosquitto), um serviço de logging para CSV e um cliente MQTT externo como o MQTTX.

O projeto demonstra, de forma simples e profissional, uma arquitetura de IoT com geração de telemetria, publicação/assinatura MQTT, detecção de alertas e persistência estruturada dos dados.

## 📁 Estrutura do Projeto

```
TP546_safeSleep/
│
├── mosquitto.conf
├── logger.py
├── safesleep_simulator.py
├── requirements.txt
├── setup_env.ps1
└── data/
      ├── telemetry.csv
      └── alerts.csv
```

## 🚀 Funcionalidades

### 🔹 Simulador IoT (`safesleep_simulator.py`)
Gera leituras fictícias a cada 3 segundos:
- Temperatura (°C)
- Umidade relativa (%)
- Nível de ruído (dB)
- Posição do bebê (supino, lateral, prono)

Regras detectam:
- Temperatura fora do recomendado
- Umidade baixa/alta
- Ruído elevado
- Posição **prona**

Publica nos tópicos:
```
safesleep/sensors/temperature
safesleep/sensors/humidity
safesleep/sensors/noise
safesleep/sensors/position
safesleep/sensors/all
safesleep/alerts
```

### 🔹 Serviço de Logging (`logger.py`)
Assina:
- `safesleep/sensors/all`
- `safesleep/alerts`

E grava:
```
data/telemetry.csv
data/alerts.csv
```

### 🔹 Broker MQTT
`mosquitto.conf` minimalista:
- Porta 1883  
- Conexões anônimas  
- Persistência desativada

## ⚙️ Configuração do Ambiente

### 🪟 Windows — Usando `setup_env.ps1`

Local do script:
```
D:\Desktop\TP546_safeSleep\setup_env.ps1
```

Executar:

```powershell
cd D:\Desktop\TP546_safeSleep
.\setup_env.ps1
```

## ▶️ Execução

### 1. Broker
```
mosquitto -c mosquitto.conf
```

### 2. Logger
```
python logger.py
```

### 3. Simulador
```
python safesleep_simulator.py
```

### 4. MQTTX
Assine:
```
safesleep/#
```

## 🧠 Arquitetura

```
Simulador → Mosquitto → Logger
                  ↳ MQTTX
```
## 🧾 Licença
Projeto didático para estudos.
