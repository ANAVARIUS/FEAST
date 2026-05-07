import logging
import requests
import os
from trello import TrelloClient
logger = logging.getLogger(__name__)

class TrelloService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = TrelloClient(
            api_key='TU_API_KEY',
            token='TU_TOKEN'
        )
            cls._instance._board = cls._instance._client.get_board(os.getenv('TRELLO_BOARD_ID'))
            cls._instance._target_list = cls._instance._board.get_list(os.getenv('TRELLO_LIST_ID'))
        return cls._instance

    def create_order(self, order, description):
        try:
            new_card = self._target_list.add_card(order, desc=description)
            logging.info(f"Tarjeta creada: {new_card.url}")
        except Exception as e:
            logging.error(f"Error al crear la tarjeta de trello: {e}")

telegram_service_instance = TrelloService()