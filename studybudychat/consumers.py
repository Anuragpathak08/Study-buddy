from django.contrib.auth import get_user_model
from .models import Message, Chat, GroupMessage, Group
from .utils import clean_text  # Assuming you move the `clean_text` function to a utils module
from django.contrib.auth import get_user_model
from .models import Message, Chat
from .utils import clean_text
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import joblib
from django.db import transaction
from django.utils.timezone import now

# Load models globally
MODEL_FILES = {
    'vectorizer': 'trained_data/tfidf_vectorizer.joblib',
    'model': 'trained_data/spam_model.joblib',
    'encoder': 'trained_data/label_encoder.joblib'
}

try:
    spam_model = joblib.load(MODEL_FILES['model'])
    tfidf_vectorizer = joblib.load(MODEL_FILES['vectorizer'])
    label_encoder = joblib.load(MODEL_FILES['encoder'])
except FileNotFoundError:
    raise Exception("Model files not found. Please train the model first.")

User = get_user_model()

class StudyBuddyMessageConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.media_metadata = None  # To store metadata for media uploads

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data:
                data = json.loads(text_data)
                if data.get('type') == 'media_metadata':
                    # Store metadata for upcoming binary data
                    self.media_metadata = data
                else:
                    # Handle text message
                    self.handle_text_message(data)
            elif bytes_data and self.media_metadata:
                # Handle media upload using stored metadata
                self.handle_media_upload(bytes_data)
        except Exception as e:
            print(f"Error: {e}")
            self.send(text_data=json.dumps({"error": str(e)}))

    def handle_text_message(self, data):
        username = data.get('username')
        message = data.get('message')
        chat_id = data.get('chat_id')

        if not username or not message:
            raise ValueError("Username and message are required")
        user = self.scope['user']
        if user.is_anonymous:
            raise PermissionError("User is not authenticated")
        if user.username != username:
            raise PermissionError("Unauthorized access")

        # Spam detection for text messages
        cleaned_text = clean_text(message)
        vectorized = tfidf_vectorizer.transform([cleaned_text])
        prediction = spam_model.predict(vectorized)[0]

        if prediction == 1:
            explanation = self.explain_with_genai(message)
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'spam_notification',
                    'message': {
                        'username': username,
                        'message': message,
                        'explanation': explanation,
                        'is_spam': True
                    }
                }
            )
            return

        # Save and broadcast legitimate text message
        chat = Chat.objects.get(id=chat_id)
        sender = User.objects.get(username=username)
        with transaction.atomic():
            message_instance = Message.objects.create(
                chat=chat,
                sender=sender,
                message_text=message
            )
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'username': username,
                    'message': message,
                    'timestamp': now().isoformat()
                }
            )

    def handle_media_upload(self, bytes_data):
        user = self.scope['user']
        if user.is_anonymous:
            raise PermissionError("User is not authenticated")

        # Use metadata sent from the client
        mime_type = self.media_metadata.get('mime_type', 'application/octet-stream')
        extension = mime_type.split('/')[-1].split(';')[0]  # Handle MIME types like "image/jpeg; charset=UTF-8"
        filename = f"chat_media/{now().strftime('%Y%m%d%H%M%S')}_{user.username}.{extension}"

        # Save the file
        media_path = default_storage.save(filename, ContentFile(bytes_data))
        media_url = default_storage.url(media_path)

        # Save media to the database and broadcast
        chat = Chat.objects.get(id=self.media_metadata['chat_id'])
        with transaction.atomic():
            message_instance = Message.objects.create(
                chat=chat,
                sender=user,
                message_text=None,
                attached_file=media_path  # Save the file path to the Message model
            )
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'username': user.username,
                    'media_url': media_url,
                    'timestamp': now().isoformat()
                }
            )
        self.media_metadata = None  # Reset metadata after processing

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'type': 'chat_message',
            'username': event.get('username'),
            'message': event.get('message'),
            'media_url': event.get('media_url'),
            'timestamp': event.get('timestamp')
        }))

    def spam_notification(self, event):
        self.send(text_data=json.dumps({
            'type': 'spam_notification',
            'username': event['message']['username'],
            'message': event['message']['message'],
            'explanation': event['message']['explanation'],
            'is_spam': True
        }))

    def explain_with_genai(self, text):
        """
        Use a Gen AI model (e.g., Groq API) to explain why a message might be spam.
        """
        prompt = f"""
        Explain why this message might be fraudulent: "{text}".
        Highlight keywords and patterns. Use simple language.
        """
        try:
            from dotenv import load_dotenv
            import os
            from groq import Groq

            load_dotenv()
            client = Groq(api_key=os.getenv('GROQ_API_KEY'))

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
        

class StudyBuddyGroupMessageConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.group_group_name = f'group_{self.group_name}'

        # Join group
        async_to_sync(self.channel_layer.group_add)(
            self.group_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        try:
            userdata = json.loads(text_data)
            username = userdata.get('username')
            message = userdata.get('message')
            group_id = userdata.get('group_id', None)

            # Validate inputs
            if not username or not message:
                raise ValueError("Username and message are required")

            user = self.scope['user']
            if user.username != username:
                raise PermissionError("Unauthorized access")

            # Check if the message is spam
            cleaned_text = clean_text(message)
            vectorized = tfidf_vectorizer.transform([cleaned_text])
            prediction = spam_model.predict(vectorized)[0]

            if prediction == 1:  # Spam detected
                explanation = self.explain_with_genai(message)  # Use Gen AI to explain why it's spam
                async_to_sync(self.channel_layer.group_send)(
                    self.group_group_name,
                    {
                        'type': 'spam_notification',
                        'message': {
                            'username': username,
                            'message': message,
                            'explanation': explanation,
                            'is_spam': True
                        }
                    }
                )
                return  # Stop further processing of the message

            # Save and broadcast the message if it's legitimate
            if group_id:
                group = Group.objects.get(id=group_id)
                sender = User.objects.get(username=username)
                with transaction.atomic():
                    message_instance = GroupMessage.objects.create(
                        group=group,
                        sender=sender,
                        message_text=message
                    )
                    async_to_sync(self.channel_layer.group_send)(
                        self.group_group_name,
                        {
                            'type': 'group_message',
                            'message': {
                                'username': username,
                                'message': message,
                                'group_id': group_id
                            }
                        }
                    )
        except Exception as e:
            # print(f"Error: {e}")
            self.send(text_data=json.dumps({"error": str(e)}))

    def group_message(self, event):
        message_data = event['message']
        self.send(text_data=json.dumps({
            'type': 'group_message',
            'username': message_data['username'],
            'message': message_data['message'],
            'group_id': message_data['group_id']
        }))

    def spam_notification(self, event):
        message_data = event['message']
        self.send(text_data=json.dumps({
            'type': 'spam_notification',
            'username': message_data['username'],
            'message': message_data['message'],
            'explanation': message_data['explanation'],
            'is_spam': True
        }))