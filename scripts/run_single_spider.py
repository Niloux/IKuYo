import sys
import os
import json
import logging
import traceback

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ikuyo.crawler.spiders.mikan import MikanSpider
from ikuyo.core.config import load_config

# Configure logging for this script
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

def run_spider(task_id: int, parameters: dict):
    """Runs a single Scrapy spider."""
    try:
        logger.info(f"Starting Scrapy spider for task {task_id} in new process.")

        # Load project configuration
        project_config = load_config()

        # Get Scrapy project settings
        settings = get_project_settings()
        settings.set("LOG_LEVEL", parameters.get("log_level", "INFO"))
        settings.set("LOG_STDOUT", False) # Ensure Scrapy logs don't go to stdout
        settings.set("LOG_ENABLED", True) # Ensure logging is enabled

        # Prepare spider arguments
        spider_kwargs = {
            "config": project_config,
            "mode": parameters.get("crawler_mode", parameters.get("mode", "homepage")),
            "task_id": task_id,
        }

        if parameters.get("year"):
            spider_kwargs["year"] = parameters["year"]
        if parameters.get("season"):
            spider_kwargs["season"] = parameters["season"]
        if parameters.get("start_url"):
            spider_kwargs["start_url"] = parameters["start_url"]
        if parameters.get("limit") is not None:
            spider_kwargs["limit"] = parameters["limit"]

        logger.info(f"Scrapy spider arguments: {spider_kwargs}")

        process = CrawlerProcess(settings)
        process.crawl(MikanSpider, **spider_kwargs)
        process.start()  # This will block until the spider finishes

        logger.info(f"Scrapy spider for task {task_id} finished.")
        return {"success": True, "message": f"Spider for task {task_id} completed."}

    except Exception as e:
        logger.error(f"Error running spider for task {task_id}: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("Usage: python run_single_spider.py <task_id> <json_parameters>")
        sys.exit(1)

    task_id = int(sys.argv[1])
    try:
        parameters = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON parameters: {e}")
        sys.exit(1)

    result = run_spider(task_id, parameters)

    # Output result as JSON to stdout for parent process to capture
    print(json.dumps(result))
    if not result["success"]:
        sys.exit(1) # Indicate failure to the parent process
