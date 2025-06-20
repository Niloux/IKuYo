# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import json
import os

from itemadapter import ItemAdapter


class IkuyoScrapyPipeline:
    def process_item(self, item, spider):
        return item


class JsonWriterPipeline:
    """将数据写入JSON文件的Pipeline"""

    def __init__(self):
        self.file = None
        self.output_dir = "output"

    def open_spider(self, spider):
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 创建输出文件
        filename = f"{self.output_dir}/mikan_data_{spider.name}.json"
        self.file = open(filename, "w", encoding="utf-8")
        self.file.write("[\n")  # 开始JSON数组
        self.first_item = True

    def close_spider(self, spider):
        if self.file is not None:
            self.file.write("\n]")  # 结束JSON数组
            self.file.close()

    def process_item(self, item, spider):
        if self.file is not None:
            if not self.first_item:
                self.file.write(",\n")
            else:
                self.first_item = False

            line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False, indent=2)
            self.file.write(line)
        return item


class DataValidationPipeline:
    """数据验证Pipeline"""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 验证必要字段
        if hasattr(item, "mikan_id") and not adapter.get("mikan_id"):
            spider.logger.warning(f"缺少mikan_id: {item}")

        if hasattr(item, "title") and not adapter.get("title"):
            spider.logger.warning(f"缺少title: {item}")

        return item
