from kafka import KafkaConsumer, KafkaProducer
from const import *
import threading

from concurrent import futures
import logging

import grpc
import iot_service_pb2
import iot_service_pb2_grpc

#############################################################

import hashlib

# Armazenar isso em um arquivo externo para leitura e escrita
users = {
    'andre':{
        'password': '7c4a8d09ca3762af61e59520943dc26494f8941b' # 123456
    }
}

# Função para registrar um usuário
def register_user(username, password):
    # Verificar se o nome de usuário já está em uso
    if username in users:
        raise ValueError("Nome de usuário já em uso.")

    # Criptografar a senha
    hashed_password = hash_password(password)

    # Armazenar as informações do usuário
    users[username] = {
        'password': hashed_password
    }

# Função para verificar a senha
def verify_password(username, password):
    if username not in users:
        return False

    stored_password = users[username]['password']
    hashed_password = hash_password(password)
    return hashed_password == stored_password

# Função para criptografar a senha
def hash_password(password):
    # Usando a função de hash SHA-1 como exemplo
    sha1 = hashlib.sha1()
    sha1.update(password.encode('utf-8'))
    hashed_password = sha1.hexdigest()
    return hashed_password

############################################################################

# Twin state
current_temperature = 'void'
current_light_level = 'void'
led_state = {'red':0, 'green':0}

# Kafka consumer to run on a separate thread
def consume_temperature():
    global current_temperature
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_SERVER+':'+KAFKA_PORT)
    consumer.subscribe(topics=('temperature'))
    for msg in consumer:
        print ('Received Temperature: ', msg.value.decode())
        current_temperature = msg.value.decode()

# Kafka consumer to run on a separate thread
def consume_light_level():
    global current_light_level
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_SERVER+':'+KAFKA_PORT)
    consumer.subscribe(topics=('lightlevel'))
    for msg in consumer:
        print ('Received Light Level: ', msg.value.decode())
        current_light_level = msg.value.decode()

def produce_led_command(state, ledname):
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER+':'+KAFKA_PORT)
    producer.send('ledcommand', key=ledname.encode(), value=str(state).encode())
    return state
        
class IoTServer(iot_service_pb2_grpc.IoTServiceServicer):

    # Autentica o usuario antes de qualquer operacao
    
    def SayTemperature(self, request, context):
    	if verify_password(request.user, request.password) == False:	
        	print("Falha na autenticação. Nome de usuário ou senha incorretos.")
 			return

    	print("Usuário autenticado com sucesso!")
        return iot_service_pb2.TemperatureReply(temperature=current_temperature)
    
    def BlinkLed(self, request, context):
		if verify_password(request.user, request.password) == False:	
	    	print("Falha na autenticação. Nome de usuário ou senha incorretos.")
 			return

    	print("Usuário autenticado com sucesso!")
        print ("Blink led ", request.ledname)
        print ("...with state ", request.state)
        produce_led_command(request.state, request.ledname)
        # Update led state of twin
        led_state[request.ledname] = request.state
        return iot_service_pb2.LedReply(ledstate=led_state)

    def SayLightLevel(self, request, context):
    	if verify_password(request.user, request.password) == False:	
        	print("Falha na autenticação. Nome de usuário ou senha incorretos.")
 			return

    	print("Usuário autenticado com sucesso!")
        return iot_service_pb2.LightLevelReply(lightLevel=current_light_level)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    iot_service_pb2_grpc.add_IoTServiceServicer_to_server(IoTServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()

    trd1 = threading.Thread(target=consume_temperature)
    trd1.start()

    trd2 = threading.Thread(target=consume_light_level)
    trd2.start()

    # Initialize the state of the leds on the actual device
    for color in led_state.keys():
        produce_led_command (led_state[color], color)
    serve()
