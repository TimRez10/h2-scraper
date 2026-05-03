import subprocess
import sys
import os
import logging
import logging.config
import yaml

# Logging Configuration
log_conf_file = "log_conf.yaml"
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

scriptList = os.listdir('./web_scraping_scripts/')

# Execute the daily scripts
for script in scriptList:
    # if script.endswith("nr-can.py"):
    #     logger.warning(f"Skipping {script}")
    #     continue
    if script.endswith('.py') and not script.startswith('__'):
        logger.info(f"\n############## RUNNING SCRIPT: {script} ##############")
        module_name = script[:-3]  # Strip the '.py'
        full_module = f'web_scraping_scripts.{module_name}'
        
        try:
            subprocess.run([sys.executable, '-m', full_module], cwd='.', check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running {script}: {e}")