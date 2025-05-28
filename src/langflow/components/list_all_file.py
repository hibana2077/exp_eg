import io
from minio import Minio
from minio.error import S3Error
from langflow.base.data import BaseFileComponent
from langflow.base.data.utils import TEXT_FILE_TYPES, parallel_load_data, parse_text_file_to_data
from langflow.io import BoolInput, IntInput, StrInput, SecretStrInput
from langflow.schema import Data