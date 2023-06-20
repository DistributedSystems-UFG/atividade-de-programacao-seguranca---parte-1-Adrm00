#from __future__ import print_function

import logging
import sys

import grpc
import iot_service_pb2
import iot_service_pb2_grpc

from const import *


def run():
    with grpc.insecure_channel(GRPC_SERVER+':'+GRPC_PORT) as channel:
        stub = iot_service_pb2_grpc.IoTServiceStub(channel)
        response = stub.SayTemperature(iot_service_pb2.TemperatureRequest(sensorName='my_sensor',username_auth=sys.argv[1],password_auth=sys.argv[2]))

    if response.state == "OK":
        print("Temperature received: " + response.temperature)
    else:
        print("Falha na autenticação. Nome de usuário ou senha incorretos.")

if __name__ == '__main__':
    logging.basicConfig()
    run()
