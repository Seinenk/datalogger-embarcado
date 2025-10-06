import smbus2
import time
import datetime
import sys
from periphery import I2C

LOGFILE = "/media/caninos/PS2-WKGAMES/dados_sensores.txt"
I2C_BUS = 2

try:
    BUS = smbus2.SMBus(I2C_BUS)
except FileNotFoundError:
    print(f"Erro: I2C {I2C_BUS} não encontrado")
    exit(1)

def bh1750_read():
    BH1750_ADDR = 0x23
    BH1750_CMD = 0x10

    data = BUS.read_i2c_block_data(BH1750_ADDR, BH1750_CMD, 2)
    # Converte os 2 bytes em um valor de luminosidade
    lux = (data[0] << 8 | data[1]) / 1.2
    return lux

I2C_BUS_PATH = "/dev/i2c-2"
i2c = I2C(I2C_BUS_PATH)

MAX30102_I2C_ADDRESS = 0x57
MAX30102_REG_MODE_CONFIG = 0x09
MAX30102_REG_SPO2_CONFIG = 0x0A
MAX30102_REG_LED_PULSE_AMP1 = 0x0C
MAX30102_REG_LED_PULSE_AMP2 = 0x0D
MAX30102_REG_FIFO_DATA = 0x07

def max30102_init():
    try:
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_MODE_CONFIG, 0x40])])
        time.sleep(0.1)
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_MODE_CONFIG, 0x03])])
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_SPO2_CONFIG, 0x67])])
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_LED_PULSE_AMP1, 0x1F])])
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_LED_PULSE_AMP2, 0x1F])])
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

def max30102_read():
    read_buf = [0] * 6
    write_msg = I2C.Message([MAX30102_REG_FIFO_DATA])
    read_msg = I2C.Message(read_buf, read=True)
    i2c.transfer(MAX30102_I2C_ADDRESS, [write_msg, read_msg])
    data = read_msg.data
    red_raw = (data[0] << 16) | (data[1] << 8) | data[2]
    ir_raw = (data[3] << 16) | (data[4] << 8) | data[5]
    return ir_raw, red_raw

if __name__ == "__main__":
    print(f"Iniciando deteccao com os sensores BH1750 e MAX30102")
    print(f"Arquivo de log: {LOGFILE}")
    print("Pressione Ctrl+C para encerrar a execucao")

    try:
        max30102_init_ok = max30102_init()

        while True:
            try:
                timestamp = datetime.datetime.now().isoformat()

                lux = bh1750_read()
                lux = f"{lux:.2f}" if lux is not None else "nao disponivel"

                print(f"({timestamp}) Luminosidade: {lux}")

                with open(LOGFILE, "a") as f:
                    f.write(f"({timestamp}) Luminosidade: {lux}")
            except Exception as e:
                print(f"Ocorreu um erro: {e}")

            if max30102_init_ok:
                try:
                    timestamp = datetime.datetime.now().isoformat()

                    valor = max30102_read()

                    print(f"({timestamp}) IR: {valor[0]} | RED: {valor[1]}")
                    with open(LOGFILE, "a") as f:
                        f.write(f"({timestamp}) IR: {valor[0]} | RED: {valor[1]}")
                except Exception as e:
                    print(f"Ocorreu um erro: {e}")

            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteccao encerrada")
    finally:
        i2c.close()
        BUS.close()
