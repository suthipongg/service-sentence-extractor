from elasticapm import Client
from config.environment import ENV
env = ENV()


client = Client({  
    'SERVICE_NAME': env.APM_SERVICE_NAME,  
    'ENVIRONMENT': env.APM_ENVIRONMENT,  # Set the environment  
    'SERVER_URL': env.APM_SERVER_URL
})  
