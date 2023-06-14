import json


class Config():

    def __init__(self) -> None:
        pass

    def load_config(
        self,
        config_file_path: str
    ):
        """
            Loading configuration file in JSON format
        Args:
            config_file_path (str):  configuration file path
        """
        file = open(config_file_path)
        
        config_dict = json.load(file)

        return config_dict
