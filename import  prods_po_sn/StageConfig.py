import os
from dotenv import load_dotenv


class StageConfig:
    """
    A class to load and store environment variables from a .env file.
    """
    def __init__(self, dotenv_path="staging.env"):
        """
        Initializes the Config class by loading environment variables from a .env file.

        Args:
            dotenv_path (str, optional): The path to the .env file. Defaults to ".env".
        """
        load_dotenv(dotenv_path=dotenv_path)  # Load variables from .env

        # Load each environment variable, and if it does not exist
        # raise an error.  You might want to modify this behavior.

        self.HOST = os.environ.get("HOST_STAGE")
        self.DB = os.environ.get("DB_STAGE")
        self.USER_EMAIL = os.environ.get("USER_EMAIL_STAGE")
        self.API_KEY = os.environ.get("API_KEY_STAGE")

        # Example of converting to a specific type (important for type safety)
        if self.HOST is None:
            raise EnvironmentError("HOST environment variable is not set.")

        if self.DB is None:
            raise EnvironmentError("DB environment variable is not set.")

        if self.USER_EMAIL is None:
            raise EnvironmentError("USER environment variable is not set.")

        if self.API_KEY is None:
            raise EnvironmentError("API_KEY environment variable is not set.")

    def __repr__(self):
        """
        Returns a string representation of the Config object.  Useful for debugging.
        """
        return (f"Config(HOST={self.HOST}, DB='{self.DB}', USER={self.USER_EMAIL}, "
                f"API_KEY='{self.API_KEY}'")
