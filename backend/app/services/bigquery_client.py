"""BigQuery client wrapper for database operations"""

from google.cloud import bigquery
from google.oauth2 import service_account
import logging
from config import settings

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Wrapper around google-cloud-bigquery for all database operations"""
    
    def __init__(self):
        """Initialize BigQuery client with credentials"""
        try:
            if settings.gcp_credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.gcp_credentials_path
                )
                self.client = bigquery.Client(
                    credentials=credentials, 
                    project=settings.gcp_project_id
                )
            else:
                self.client = bigquery.Client(project=settings.gcp_project_id)
            
            logger.info(f"BigQuery client initialized for project: {settings.gcp_project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {str(e)}")
            raise
    
    def load_csv_to_table(self, csv_file_path: str, dataset_id: str, table_id: str):
        """Load CSV file to BigQuery table"""
        try:
            table_id_full = f"{settings.gcp_project_id}.{dataset_id}.{table_id}"
            
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=1,
                autodetect=True,
                write_disposition="WRITE_TRUNCATE"
            )
            
            with open(csv_file_path, "rb") as source_file:
                load_job = self.client.load_table_from_file(
                    source_file,
                    table_id_full,
                    job_config=job_config
                )
            
            load_job.result(timeout=600)
            
            logger.info(f"Loaded {load_job.output_rows} rows to {table_id_full}")
            return {"rows_loaded": load_job.output_rows}
        
        except Exception as e:
            logger.error(f"Failed to load CSV: {str(e)}")
            raise
    
    def execute_query(self, query: str, dataset_id: str = None) -> list:
        """Execute SQL query and return results"""
        try:
            job_config = bigquery.QueryJobConfig()
            if dataset_id:
                job_config.default_dataset = f"{settings.gcp_project_id}.{dataset_id}"
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result(timeout=600)
            
            logger.info(f"Query executed successfully")
            return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
