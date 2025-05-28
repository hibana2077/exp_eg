import io
from minio import Minio
from minio.error import S3Error
from langflow.base.data import BaseFileComponent
from langflow.base.data.utils import TEXT_FILE_TYPES, parallel_load_data, parse_text_file_to_data
from langflow.io import BoolInput, IntInput, StrInput, SecretStrInput
from langflow.schema import Data


class MinIOFileComponent(BaseFileComponent):
    """Handles loading and processing of individual or zipped text files from MinIO.

    This component supports processing multiple valid files from MinIO buckets,
    validating file types, and optionally using multithreading for processing.
    """

    display_name = "MinIO File"
    description = "Load files from MinIO bucket to be used in your project."
    icon = "cloud"
    name = "MinIOFile"

    VALID_EXTENSIONS = TEXT_FILE_TYPES

    inputs = [
        StrInput(
            name="endpoint",
            display_name="MinIO Endpoint",
            info="MinIO server endpoint (e.g., localhost:9000)",
            required=True,
        ),
        StrInput(
            name="access_key",
            display_name="Access Key",
            info="MinIO access key",
            required=True,
        ),
        SecretStrInput(
            name="secret_key",
            display_name="Secret Key",
            info="MinIO secret key",
            required=True,
        ),
        StrInput(
            name="bucket_name",
            display_name="Bucket Name",
            info="MinIO bucket name",
            required=True,
        ),
        StrInput(
            name="object_path",
            display_name="Object Path",
            info="Path to the file in the bucket (e.g., folder/file.txt)",
            required=True,
        ),
        BoolInput(
            name="secure",
            display_name="Use HTTPS",
            info="Use HTTPS for connection",
            value=True,
        ),
        BoolInput(
            name="use_multithreading",
            display_name="[Deprecated] Use Multithreading",
            advanced=True,
            value=True,
            info="Set 'Processing Concurrency' greater than 1 to enable multithreading.",
        ),
        IntInput(
            name="concurrency_multithreading",
            display_name="Processing Concurrency",
            advanced=True,
            info="When multiple files are being processed, the number of files to process concurrently.",
            value=1,
        ),
    ]

    outputs = [
        *BaseFileComponent._base_outputs,
    ]

    def get_minio_client(self) -> Minio:
        """Creates and returns a MinIO client."""
        return Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

    def download_file_from_minio(self, object_path: str) -> io.BytesIO:
        """Downloads a file from MinIO and returns it as BytesIO."""
        try:
            client = self.get_minio_client()
            response = client.get_object(self.bucket_name, object_path)
            return io.BytesIO(response.read())
        except S3Error as e:
            msg = f"Error downloading file from MinIO: {e}"
            self.log(msg)
            raise
        finally:
            if 'response' in locals():
                response.close()

    def process_files(self, file_list: list[str]) -> list[Data]:
        """Processes files from MinIO either sequentially or in parallel.

        Args:
            file_list (list[str]): List of object paths to process from MinIO.

        Returns:
            list[Data]: List of processed Data objects.
        """

        def process_file(object_path: str, *, silent_errors: bool = False) -> Data | None:
            """Downloads and processes a single file from MinIO."""
            try:
                file_content = self.download_file_from_minio(object_path)
                # Convert BytesIO to string for text processing
                text_content = file_content.getvalue().decode('utf-8')
                
                # Create Data object with file content
                data = Data(
                    text=text_content,
                    data={"source": f"minio://{self.bucket_name}/{object_path}"}
                )
                return data
            except Exception as e:
                msg = f"Unexpected error processing {object_path}: {e}"
                self.log(msg)
                if not silent_errors:
                    raise
                return None

        if not file_list:
            # If no file list provided, use the single object_path
            file_list = [self.object_path]

        if not file_list:
            msg = "No files to process."
            raise ValueError(msg)

        concurrency = 1 if not self.use_multithreading else max(1, self.concurrency_multithreading)
        file_count = len(file_list)

        parallel_processing_threshold = 2
        if concurrency < parallel_processing_threshold or file_count < parallel_processing_threshold:
            if file_count > 1:
                self.log(f"Processing {file_count} files sequentially from MinIO.")
            processed_data = [process_file(object_path, silent_errors=self.silent_errors) for object_path in file_list]
        else:
            self.log(f"Starting parallel processing of {file_count} files from MinIO with concurrency: {concurrency}.")
            processed_data = parallel_load_data(
                file_list,
                silent_errors=self.silent_errors,
                load_function=process_file,
                max_concurrency=concurrency,
            )

        # Filter out None values
        return [data for data in processed_data if data is not None]
