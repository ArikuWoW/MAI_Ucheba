import time
from pymongo import MongoClient
from passlib.context import CryptContext

# Настройка MongoDB
MONGO_URI = "mongodb://root:pass@mongo:27017/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["conference_db"]
mongo_users_collection = mongo_db["users"]

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def load_test_data():
    def add_user(username, email, hashed_password):
        user = mongo_users_collection.find_one({"username": username})
        if not user:
            user = {
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
            }
            mongo_users_collection.insert_one(user)

    add_user("admin", "admin@example.com", pwd_context.hash("adminpass"))
    add_user("user1", "user1@example.com", pwd_context.hash("user1pass"))

def wait_for_db(retries=10, delay=5):
    for _ in range(retries):
        try:
            mongo_client.admin.command("ismaster")
            print("MongoDB is ready!")
            return
        except Exception as e:
            print(f"Waiting for MongoDB: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to MongoDB")

if __name__ == "__main__":
    wait_for_db()
    load_test_data()
