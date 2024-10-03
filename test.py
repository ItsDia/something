import logging
from milvus import default_server
from pymilvus import connections, Collection

logging.basicConfig(level=logging.INFO)

class milvusClient:
    def __init__(self):
        try:
            default_server.start(timeout=60.0)  # 设置超时时间为60秒
            logging.info("Milvus server started successfully.")
        except Exception as e:
            logging.error(f"Error starting Milvus server: {e}")
            try:
                default_server.cleanup()  # 清理已存在的服务
            except RuntimeError as cleanup_error:
                logging.warning(f"Cleanup error: {cleanup_error}")

        connections.connect(host='127.0.0.1', port=default_server.listen_port)
        self.collection = None
        def createCollection(self):
            collection_name = "qadb"
            self.collection = Collection(collection_name)
            logging.info(f"Collection '{collection_name}' created successfully.")

        def load(self):
            self.collection.load()
            logging.info("Collection loaded successfully.")


mc = milvusClient()
