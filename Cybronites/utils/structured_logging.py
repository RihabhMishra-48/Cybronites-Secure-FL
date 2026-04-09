import logging
import json
import os
import time
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    Custom Formatter that outputs log records as JSON.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
            "epoch": record.created
        }
        
        # Include any extra fields passed in 'extra' parameter
        # but avoid standard reserved attributes
        standard_attrs = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                log_record[key] = value
                
        # Ensure the output is a single line with no trailing commas or pretty-printing
        return json.dumps(log_record, separators=(',', ':'))

def setup_structured_logging(logger_name, log_file="backend.json"):
    """
    Attaches a JSON FileHandler to the specified logger.
    """
    # Ensure project root for log file
    # We want backend.json in the projects root
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(root, log_file)
    
    logger = logging.getLogger(logger_name)
    
    # Check if handler already exists to avoid duplicates in multi-import scenarios
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == os.path.abspath(json_path):
            return logger

    # Create handler
    handler = logging.FileHandler(json_path, mode='a')
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger
