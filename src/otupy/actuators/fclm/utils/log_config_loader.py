import os, json, logging
from otupy.profiles.fclm.data.ef import EF
from otupy import ArrayOf

# define Nothing as a string
from dotenv import load_dotenv

DEFAULT_EXPORT_FIELDS_FILE="../defaults/export_fields.json"

load_dotenv()  # Load environment variables from .env
Empty = ["Nothing"]
logger = logging.getLogger(__name__)

class LogConfigLoader:

    def __init__(self, capabilities, export_fields):
       """
          Load configurations from a dictionary
       """
       self.capabilities = capabilities
       self.export_fields = export_fields if export_fields else self._load_config(DEFAULT_EXPORT_FIELDS_FILE)

    def _load_config(self, config_filename):
        """
        Load log configuration from a JSON file and return specific details based feature_name.
        """
        try:
            config_path = os.path.join(os.path.dirname(__file__), config_filename)
            with open(config_path, "r") as f:
                config = json.load(f)
                if config:
                    return config
                else:
                    return None
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load config: {e}")
            return None

    def get_feature(self, feature_name):
        """
        Query for a specific feature.
        :param feature_name: The name of the feature to query (e.g., "import_configs").
        :return: The feature value or Nothing if the feature is not found.
        """
        if self.capabilities:
            feature_value = self.capabilities.get(feature_name)
            if feature_value:
                return feature_value
        return Empty  # Empy capabilities or Feature not found

    def get_export_fields(self, ef_names_to_return: ArrayOf = None):
        """
        Get the information elements (EF) for the agent.
        If specific ef_names are provided, return those agent-specific EFs, else return the general EFs.

        :param ef_names_to_return: A list of specific ef_names to return, or None to return all general efs.
        :return: A tuple of (ArrayOf(EF), list of ef_names) or an error message if any element is not found.
        """
        agent = self.get_feature(feature_name="agent")
        if agent == Empty:
            return Empty

        efs = ArrayOf(EF)()
        ef_names = []

        if ef_names_to_return is not None:
            # If the specific ef_names_to_return list is provided
            for ef_name in ef_names_to_return:
                # Look for the ef name in the configuration
                if ef_name in self.export_fields:
                    agent_map = self.export_fields[ef_name]
                    if agent in agent_map:
                        ef_names.append(agent_map[agent])  # Add the agent-specific EF
                    else:
                        return None
                else:
                    return None
            return ef_names
        else:
            # If no specific ef_names are provided, return general EFs
            for ef_name, agent_map in self.export_fields.items():
                if agent in agent_map:
                    efs.append(EF(ef_name))  # Collect general ef_names
            return efs  # Return both the populated ArrayOf(EF) and list of ef_names
