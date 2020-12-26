from random import choice

import time
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def randomWait(min, max):
    wait = choice([i for i in range(min, max)])
    logging.info(f"Wait for {wait} seconds")
    time.sleep(wait)