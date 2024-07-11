import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='zeruel.log', filemode='w', level=logging.DEBUG)

# TODO: maybe in zeruel.py we can add exec args to change logging level