import json
import boto3
import logging
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SENSITIVE_FIELDS = {'password', 'credit_card', 'token', 'secret'}

def sanitize_event(event: dict) -> dict:
    return {k: '***' if k in SENSITIVE_FIELDS else v for k, v in event.items()}

def validate_user_id(user_id) -> str:
    if not isinstance(user_id, str) or not re.match(r'^[a-zA-Z0-9_-]{1,64}$', user_id):
        raise ValueError(f"user_id inválido: {user_id!r}")
    return user_id

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')

def lambda_handler(event, context):
    logger.info(f"Evento recibido: {json.dumps(sanitize_event(event))}")

    user_id = validate_user_id(event.get('user_id'))

    response = table.get_item(Key={'user_id': user_id})
    user = response.get('Item', {})

    email = user.get('email')
    logger.info(f"Procesando usuario ID: {user_id}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'email': email,
            'message': 'Usuario procesado correctamente'
        })
    }
