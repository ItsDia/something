from milvus import default_server
from pymilvus import connections, utility, Collection
from pymilvus import CollectionSchema, FieldSchema, DataType
import logging

logging.basicConfig(level=logging.INFO)


class milvusClient:
    def __init__(self):
        try:
            default_server.start()
        except Exception as e:
            logging.error(f"Error starting Milvus server: {e}")
            default_server.cleanup()  # 清理已存在的服务
            default_server.start()  # 重新启动

        self.collection = None
        connections.connect(host='127.0.0.1', port=default_server.listen_port)

    def createCollection(self):
        # No need to connect again
        answer_id = FieldSchema(
            name="answer_id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )
        answer = FieldSchema(
            name="answer",
            dtype=DataType.VARCHAR,
            max_length=5000,
        )
        answer_vector = FieldSchema(
            name="answer_vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=384
        )

        schema = CollectionSchema(
            fields=[answer_id, answer, answer_vector],
            description="vector data"
        )

        collection_name = "qadb"

        # 创建集合
        Collection(
            name=collection_name,
            schema=schema,
            using='default',
            shards_num=2
        )

        self.collection = Collection(collection_name)  # 使用新创建的集合

    def load(self):
        connections.connect(host='127.0.0.1', port=default_server.listen_port)
        self.collection = Collection("qadb")
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }

        self.collection.create_index(
            field_name="answer_vector",
            index_params=index_params
        )
        utility.index_building_progress("qadb")

        self.collection.load()

    def insert(self, text, embedding):
        data = [
            [text],
            embedding
        ]
        self.collection.insert(data)

    def search(self, embedding):
        search_params = {
            "metric_type": "L2",
            "offset": 0,
            "ignore_growing": False,
            "params": {"nprobe": 10}
        }

        results = self.collection.search(
            data=embedding,
            anns_field="answer_vector",
            param=search_params,
            limit=1,
            expr=None,
            output_fields=['answer'],
            consistency_level="Strong"
        )
        try:
            answer = results[0][0].entity.get('answer')
            logging.info("【数据检索】 {}".format(answer))
            return answer
        except:
            return "未找到相关结果"
