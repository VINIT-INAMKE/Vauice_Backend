"""
Encryption utilities for end-to-end encrypted chat
This module provides server-side utilities for managing encryption keys
and supporting client-side encryption operations.

Note: The actual message encryption/decryption happens on the client side.
The server only stores encrypted content and manages public keys.
"""

import base64
import hashlib
import secrets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """
    Server-side encryption utilities for supporting E2E encryption
    """
    
    @staticmethod
    def generate_key_pair():
        """
        Generate RSA key pair for encryption
        Returns: (private_key_pem, public_key_pem)
        """
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize keys to PEM format
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return (
                base64.b64encode(private_pem).decode('utf-8'),
                base64.b64encode(public_pem).decode('utf-8')
            )
            
        except Exception as e:
            logger.error(f"Error generating key pair: {str(e)}")
            raise
    
    @staticmethod
    def validate_public_key(public_key_b64):
        """
        Validate a base64 encoded public key
        """
        try:
            public_key_pem = base64.b64decode(public_key_b64)
            serialization.load_pem_public_key(public_key_pem, backend=default_backend())
            return True
        except Exception as e:
            logger.error(f"Invalid public key: {str(e)}")
            return False
    
    @staticmethod
    def generate_content_hash(content):
        """
        Generate SHA-256 hash of content for integrity verification
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def generate_key_id(user_id, timestamp=None):
        """
        Generate a unique key ID for a user
        """
        if timestamp is None:
            from django.utils import timezone
            timestamp = timezone.now().isoformat()
        
        data = f"{user_id}_{timestamp}_{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    @staticmethod
    def encrypt_file_metadata(filename, file_size, content_type):
        """
        Encrypt file metadata (if needed for additional security)
        This is optional and depends on security requirements
        """
        try:
            # Simple XOR encryption for metadata (can be enhanced)
            key = settings.SECRET_KEY[:32].encode()
            
            metadata = f"{filename}|{file_size}|{content_type}"
            metadata_bytes = metadata.encode('utf-8')
            
            encrypted = bytes(a ^ b for a, b in zip(metadata_bytes, key * (len(metadata_bytes) // len(key) + 1)))
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encrypting file metadata: {str(e)}")
            return None
    
    @staticmethod
    def decrypt_file_metadata(encrypted_metadata):
        """
        Decrypt file metadata
        """
        try:
            key = settings.SECRET_KEY[:32].encode()
            encrypted_bytes = base64.b64decode(encrypted_metadata)
            
            decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key * (len(encrypted_bytes) // len(key) + 1)))
            metadata = decrypted.decode('utf-8')
            
            parts = metadata.split('|')
            if len(parts) == 3:
                return {
                    'filename': parts[0],
                    'file_size': int(parts[1]),
                    'content_type': parts[2]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error decrypting file metadata: {str(e)}")
            return None

class MessageEncryption:
    """
    Utilities for message encryption support
    Note: Actual encryption happens on client side
    """
    
    @staticmethod
    def validate_encrypted_message(encrypted_content, content_hash):
        """
        Validate that the encrypted content matches the provided hash
        """
        try:
            if not encrypted_content or not content_hash:
                return False
            
            # Calculate hash of encrypted content
            calculated_hash = EncryptionManager.generate_content_hash(encrypted_content)
            return calculated_hash == content_hash
            
        except Exception as e:
            logger.error(f"Error validating encrypted message: {str(e)}")
            return False
    
    @staticmethod
    def generate_message_signature(message_data, user_private_key=None):
        """
        Generate a signature for message integrity (optional)
        This can be used for additional verification
        """
        try:
            # This is a placeholder for message signing
            # In a full implementation, you might want to sign messages
            # for additional integrity verification
            message_string = f"{message_data.get('content', '')}{message_data.get('timestamp', '')}"
            return EncryptionManager.generate_content_hash(message_string)
            
        except Exception as e:
            logger.error(f"Error generating message signature: {str(e)}")
            return None

class KeyExchange:
    """
    Utilities for managing key exchange between users
    """
    
    @staticmethod
    def prepare_key_bundle(user, public_key):
        """
        Prepare a key bundle for sharing with other users
        """
        try:
            from .models import EncryptionKey
            
            # Validate the public key
            if not EncryptionManager.validate_public_key(public_key):
                raise ValueError("Invalid public key format")
            
            # Generate key ID
            key_id = EncryptionManager.generate_key_id(user.id)
            
            # Create key bundle
            key_bundle = {
                'user_id': str(user.id),
                'username': user.username,
                'key_id': key_id,
                'public_key': public_key,
                'timestamp': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None
            }
            
            return key_bundle
            
        except Exception as e:
            logger.error(f"Error preparing key bundle: {str(e)}")
            return None
    
    @staticmethod
    def verify_key_bundle(key_bundle):
        """
        Verify a key bundle from another user
        """
        try:
            required_fields = ['user_id', 'key_id', 'public_key']
            
            # Check required fields
            for field in required_fields:
                if field not in key_bundle:
                    return False
            
            # Validate public key
            return EncryptionManager.validate_public_key(key_bundle['public_key'])
            
        except Exception as e:
            logger.error(f"Error verifying key bundle: {str(e)}")
            return False

class SecurityUtils:
    """
    Additional security utilities for chat system
    """
    
    @staticmethod
    def generate_room_encryption_seed(room_id, participants):
        """
        Generate a deterministic seed for room-based encryption
        This can be used for group chat encryption
        """
        try:
            # Sort participant IDs for consistency
            participant_ids = sorted([str(p.id) for p in participants])
            seed_data = f"{room_id}_{'_'.join(participant_ids)}"
            
            return hashlib.sha256(seed_data.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Error generating room encryption seed: {str(e)}")
            return None
    
    @staticmethod
    def validate_message_integrity(message):
        """
        Validate message integrity using stored hash
        """
        try:
            if not message.encrypted_content or not message.content_hash:
                return False
            
            calculated_hash = EncryptionManager.generate_content_hash(message.encrypted_content)
            return calculated_hash == message.content_hash
            
        except Exception as e:
            logger.error(f"Error validating message integrity: {str(e)}")
            return False
    
    @staticmethod
    def clean_expired_keys():
        """
        Clean up expired encryption keys
        This should be run periodically as a maintenance task
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            from .models import EncryptionKey
            
            # Remove keys older than 90 days that are inactive
            expiry_date = timezone.now() - timedelta(days=90)
            
            expired_keys = EncryptionKey.objects.filter(
                created_at__lt=expiry_date,
                is_active=False
            )
            
            count = expired_keys.count()
            expired_keys.delete()
            
            logger.info(f"Cleaned up {count} expired encryption keys")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning expired keys: {str(e)}")
            return 0
