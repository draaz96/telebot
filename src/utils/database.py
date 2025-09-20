import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from bson import ObjectId

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGODB_URI')
        if not self.mongo_uri:
            raise ValueError("MongoDB URI not found in environment variables")
        
        try:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client.get_database('filebot')
            self.files = self.db.get_collection('files')
            self.users = self.db.get_collection('users')
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise

    async def save_file(self, file_data: dict) -> str:
        """
        Save file information to database
        Returns: Document ID
        """
        try:
            result = await self.files.insert_one({
                **file_data,
                'downloads': 0,
                'created_at': datetime.utcnow()
            })
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to save file data: {str(e)}")
            raise

    async def get_file(self, file_id: str) -> dict:
        """
        Retrieve file information from database
        """
        try:
            return await self.files.find_one({'_id': ObjectId(file_id)})
        except Exception as e:
            logger.error(f"Failed to retrieve file data: {str(e)}")
            raise

    async def update_download_count(self, file_id: str):
        """
        Increment download count for a file
        """
        try:
            await self.files.update_one(
                {'_id': ObjectId(file_id)},
                {'$inc': {'downloads': 1}}
            )
        except Exception as e:
            logger.error(f"Failed to update download count: {str(e)}")

    async def delete_expired_files(self):
        """
        Delete files that are older than 2 hours
        """
        try:
            expiry_time = datetime.utcnow() - timedelta(hours=2)
            result = await self.files.delete_many({
                'created_at': {'$lt': expiry_time}
            })
            if result.deleted_count > 0:
                logger.info(f"Deleted {result.deleted_count} expired files")
        except Exception as e:
            logger.error(f"Failed to delete expired files: {str(e)}")

    async def save_user_activity(self, user_id: int, activity_type: str, file_id: str = None):
        """
        Track user activity
        """
        try:
            await self.users.update_one(
                {'user_id': user_id},
                {
                    '$push': {
                        'activities': {
                            'type': activity_type,
                            'file_id': file_id,
                            'timestamp': datetime.utcnow()
                        }
                    },
                    '$setOnInsert': {'created_at': datetime.utcnow()}
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to save user activity: {str(e)}")

    async def check_connection(self) -> bool:
        """
        Check if database connection is alive
        """
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False