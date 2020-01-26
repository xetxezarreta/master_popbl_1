import json
import pika
import logging
from os import environ
import ssl
from datetime import datetime
from .config import Config

logging.basicConfig()

config = Config.get_instance()

ssl.match_hostname = lambda cert, hostname: True

MACHINE_EXCHANGE = "machine_events"

class Publisher(object):

    def __init__(self, reply_exchange=None, reply_topic=None):
        self.create_connection()
        self.reply_exchange=reply_exchange
        self.reply_topic=reply_topic

    def create_connection(self):
        context = ssl.create_default_context(
            cafile=config.CA_CERTS)
        context.load_cert_chain(config.CERTFILE,
                                config.KEYFILE)
        ssl_options = pika.SSLOptions(context, config.RABBITMQ_IP)

        credentials = pika.PlainCredentials(
            config.RABBITMQ_USER, config.RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            ssl_options=ssl_options,
            host=config.RABBITMQ_IP, port=config.RABBITMQ_PORT, virtual_host='/', credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        # Default exchanges declared
        channel.exchange_declare(exchange=MACHINE_EXCHANGE, exchange_type='topic')
        channel.exchange_declare(exchange="LogExchange", exchange_type='topic')
        self.connection = connection
        self.channel = channel

    def close(self):
        self.connection.close()

    def send_reserve_response(self, order_id, response, pub_exchange, pub_topic):
            body = {"publisherCode": "MACHINE", "orderId": order_id, "response": response}

            self.channel.exchange_declare(exchange=pub_exchange, exchange_type='topic')

            self.channel.basic_publish(exchange=pub_exchange,
                            routing_key=pub_topic,
                            body=json.dumps(body))
            self.send_log("Machine Reserve Response: " + str(body))

            print(" [x] Sent " + str(body) + "to " + pub_topic + " topic")


    def send_cancel_order_response(self, order_id, response, pub_exchange, pub_topic):
            body = {"publisherCode": "MACHINE", "orderId": order_id, "response": response}

            self.channel.exchange_declare(exchange=pub_exchange, exchange_type='topic')

            self.channel.basic_publish(exchange=pub_exchange,
                            routing_key=pub_topic,
                            body=json.dumps(body))
            self.send_log("CancelOrder  Response: " + str(body))

            print(" [x] Sent " + str(body) + "to " + pub_topic + " topic")



    def send_log(self, msg):
        log_msg = dict()
        log_msg["timestamp"] = str(datetime.now())
        log_msg["level"] = "INFO"
        log_msg["service_name"] = "Delivery"
        log_msg["msg"] = msg

        self.channel.basic_publish(exchange="LogExchange",
                            routing_key="INFO",
                            body=json.dumps(log_msg))


    def publish_order_finished(self, order_id):
        body = {"orderId": order_id}

        self.channel.basic_publish(exchange=MACHINE_EXCHANGE,
                         routing_key="machine.finished_orders",
                         body=json.dumps(body))

        self.send_log("Machine publish order finished : " + str(body))

        print(" [x] Sent " + str(body) + "to machine.finished_orders topic")