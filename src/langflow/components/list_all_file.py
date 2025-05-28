import io
import requests
from langflow.base.data import BaseFileComponent
from langflow.base.data.utils import TEXT_FILE_TYPES, parallel_load_data, parse_text_file_to_data
from langflow.io import BoolInput, IntInput, StrInput, SecretStrInput
from langflow.schema import Data


class ListAllFilesComponent(BaseFileComponent):