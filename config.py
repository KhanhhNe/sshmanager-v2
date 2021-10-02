import configparser


def default_config():
    config = configparser.ConfigParser()
    config['SSH'] = {
        'tasks_count': 20,
    }
    config['PORT'] = {
        'tasks_count': 20,
    }
    config['WEB'] = {
        'workers': 5,
        'port': 6080,
    }
    return config


def get_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not config.sections():
        config = default_config()
        write_config(config)
    return config


def write_config(config):
    with open('config.ini', 'w+') as file:
        config.write(file)
