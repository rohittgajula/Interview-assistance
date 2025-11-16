import redis
from pybloom_live import BloomFilter
import pickle
import logging
from typing import cast
from django.conf import settings

logger = logging.getLogger(__name__)

class BloomFilterService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.username_key = 'bloom_filter:usernames'
        self.email_key = 'bloom_filter:emails'
        self.capacity = settings.BLOOM_FILTER_CAPACITY
        self.error_rate = settings.BLOOM_FILTER_ERROR_RATE
        
    def _get_bloom_filter(self, key):
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(cast(bytes, data))
            else:
                # Create new bloom filter
                bloom_filter = BloomFilter(capacity=self.capacity, error_rate=self.error_rate)
                self._save_bloom_filter(key, bloom_filter)
                return bloom_filter
        except Exception as e:
            logger.error(f"Error getting bloom filter {key}: {e}")
            # Return new bloom filter on error
            return BloomFilter(capacity=self.capacity, error_rate=self.error_rate)
    
    def _save_bloom_filter(self, key, bloom_filter):
        try:
            data = pickle.dumps(bloom_filter)
            self.redis_client.set(key, data)
        except Exception as e:
            logger.error(f"Error saving bloom filter {key}: {e}")
    
    def add_username(self, username):
        if not username:
            return False
        
        try:
            bloom_filter = self._get_bloom_filter(self.username_key)
            bloom_filter.add(username.lower())
            self._save_bloom_filter(self.username_key, bloom_filter)
            logger.info(f"Added username to bloom filter: {username}")
            return True
        except Exception as e:
            logger.error(f"Error adding username {username}: {e}")
            return False
    
    def add_email(self, email):
        if not email:
            return False
        
        try:
            bloom_filter = self._get_bloom_filter(self.email_key)
            bloom_filter.add(email.lower())
            self._save_bloom_filter(self.email_key, bloom_filter)
            logger.info(f"Added email to bloom filter: {email}")
            return True
        except Exception as e:
            logger.error(f"Error adding email {email}: {e}")
            return False
    
    def check_username(self, username):
        if not username:
            return False
        
        try:
            bloom_filter = self._get_bloom_filter(self.username_key)
            result = username.lower() in bloom_filter
            logger.info(f"Username check for {username}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error checking username {username}: {e}")
            return False
    
    def check_email(self, email):
        if not email:
            return False
        
        try:
            bloom_filter = self._get_bloom_filter(self.email_key)
            result = email.lower() in bloom_filter
            logger.info(f"Email check for {email}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error checking email {email}: {e}")
            return False
    
    def clear_usernames(self):

        try:
            self.redis_client.delete(self.username_key)
            logger.info("Cleared username bloom filter")
            return True
        except Exception as e:
            logger.error(f"Error clearing username bloom filter: {e}")
            return False
    
    def clear_emails(self):
        try:
            self.redis_client.delete(self.email_key)
            logger.info("Cleared email bloom filter")
            return True
        except Exception as e:
            logger.error(f"Error clearing email bloom filter: {e}")
            return False
    
    def clear_all(self):

        username_result = self.clear_usernames()
        email_result = self.clear_emails()
        return username_result and email_result
    
    def get_stats(self):
        try:
            username_filter = self._get_bloom_filter(self.username_key)
            email_filter = self._get_bloom_filter(self.email_key)
            
            return {
                'username_filter': {
                    'capacity': username_filter.capacity,
                    'count': username_filter.count,
                    'error_rate': username_filter.error_rate
                },
                'email_filter': {
                    'capacity': email_filter.capacity,
                    'count': email_filter.count,
                    'error_rate': email_filter.error_rate
                }
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

# global instance
bloom_service = BloomFilterService()