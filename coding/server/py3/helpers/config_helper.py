import utilities
from helpers.logging_helper import logger

class Config:
    srv_host        : str
    srv_port        : int
    srv_debug       : bool
    srv_drivers     : str

    db_name         : str
    db_host         : str
    db_user         : str
    db_password     : str

    nao_ip          : str
    nao_port        : int
    nao_user        : str
    nao_password    : str

    nao_ip_2        : str
    nao_port_2      : int
    nao_user_2      : str
    nao_password_2  : str

    def __init__(self):
        configuration = utilities.read_yaml('config.yaml')
        #configuration = utilities.read_yaml('configLAN.yaml')
        
        logger.info("Loaded configuration: {}".format(configuration))
        self.load_config(configuration)

    def load_config(self, config):
        self.srv_debug      = config['server']['debug']
        self.srv_host       = config['server']['host']
        self.srv_port       = config['server']['port']
        self.srv_drivers    = config['server']['drivers']

        self.db_host        = config['database']['host']
        self.db_name        = config['database']['name']
        self.db_user        = config['database']['user']
        self.db_password    = config['database']['password']

        self.nao_ip         = config['nao']['ip']
        self.nao_port       = config['nao']['port']
        self.nao_user       = config['nao']['user']
        self.nao_password   = config['nao']['password']
        self.nao_api_openai = config['nao']['api_openai']

        self.nao_ip_2       = config['nao2']['ip']
        self.nao_port_2     = config['nao2']['port']
        self.nao_user_2     = config['nao2']['user']
        self.nao_password_2 = config['nao2']['password']
