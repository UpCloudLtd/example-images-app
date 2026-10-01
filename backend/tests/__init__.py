import os

# Set before the app is imported so tests never touch the default table or bucket.
os.environ["IMAGES_TABLE"] = "images_test"
os.environ["GENERATORS_TABLE"] = "generators_test"
os.environ["OBJSTO_BUCKET"] = "images-test"
os.environ["GENERATOR_TOKEN"] = "test-token"
