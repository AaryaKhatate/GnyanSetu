# Voice Synthesis Service for Natural Language Teaching
import logging
import os
import asyncio
import uuid
from typing import Dict, Optional
import gtts
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

class VoiceSynthesisService:
    """Advanced voice synthesis service with multiple TTS engines"""
    
    def __init__(self):
        self.voice_settings = settings.VOICE_SETTINGS
        self.media_root = settings.MEDIA_ROOT
        self.tts_engine = self.voice_settings.get('TTS_ENGINE', 'azure')
        
        # Ensure media directory exists
        os.makedirs(os.path.join(self.media_root, 'voice'), exist_ok=True)
    
    async def synthesize_speech(self, text: str, voice_settings: Dict = None, session_id: str = None) -> str:
        """
        Synthesize speech from text using the configured TTS engine
        Returns URL to the generated audio file
        """
        try:
            # Merge voice settings
            settings_to_use = {**self.voice_settings, **(voice_settings or {})}
            
            # Generate unique filename
            audio_filename = f"voice_{uuid.uuid4().hex}.wav"
            audio_path = os.path.join(self.media_root, 'voice', audio_filename)
            
            # Choose TTS engine
            engine = settings_to_use.get('TTS_ENGINE', self.tts_engine)
            
            if engine == 'azure':
                success = await self._synthesize_azure(text, audio_path, settings_to_use)
            elif engine == 'openai':
                success = await self._synthesize_openai(text, audio_path, settings_to_use)
            elif engine == 'gtts':
                success = await self._synthesize_gtts(text, audio_path, settings_to_use)
            else:
                logger.error(f"Unknown TTS engine: {engine}")
                return None
            
            if success:
                # Return URL relative to media root
                audio_url = f"/media/voice/{audio_filename}"
                logger.info(f"Voice synthesized successfully: {audio_url}")
                return audio_url
            else:
                logger.error("Voice synthesis failed")
                return None
                
        except Exception as e:
            logger.error(f"Error in voice synthesis: {e}")
            return None
    
    async def _synthesize_azure(self, text: str, output_path: str, settings: Dict) -> bool:
        """Synthesize using Azure Cognitive Services (Premium quality)"""
        try:
            speech_key = settings.get('AZURE_SPEECH_KEY')
            speech_region = settings.get('AZURE_SPEECH_REGION')
            
            if not speech_key or not speech_region:
                logger.warning("Azure Speech credentials not configured, falling back to GTTS")
                return await self._synthesize_gtts(text, output_path, settings)
            
            # Configure speech service
            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key, 
                region=speech_region
            )
            
            # Set voice and language
            voice_name = self._get_azure_voice_name(settings)
            speech_config.speech_synthesis_voice_name = voice_name
            
            # Set speech rate and pitch
            ssml_text = self._create_ssml(text, settings)
            
            # Configure audio output
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # Synthesize speech
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("Azure TTS synthesis completed successfully")
                return True
            else:
                logger.error(f"Azure TTS failed: {result.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Azure TTS error: {e}")
            return await self._synthesize_gtts(text, output_path, settings)
    
    async def _synthesize_openai(self, text: str, output_path: str, settings: Dict) -> bool:
        """Synthesize using OpenAI TTS"""
        try:
            import openai
            
            api_key = settings.get('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OpenAI API key not configured, falling back to GTTS")
                return await self._synthesize_gtts(text, output_path, settings)
            
            client = openai.OpenAI(api_key=api_key)
            
            # Generate speech
            response = client.audio.speech.create(
                model="tts-1-hd",  # High quality model
                voice=settings.get('DEFAULT_VOICE', 'alloy'),
                input=text,
                speed=settings.get('SPEECH_SPEED', 1.0)
            )
            
            # Save audio file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info("OpenAI TTS synthesis completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return await self._synthesize_gtts(text, output_path, settings)
    
    async def _synthesize_gtts(self, text: str, output_path: str, settings: Dict) -> bool:
        """Synthesize using Google Text-to-Speech (Fallback)"""
        try:
            language = settings.get('VOICE_LANGUAGE', 'en')
            speed = settings.get('SPEECH_SPEED', 1.0)
            
            # Create TTS object
            tts = gtts.gTTS(text=text, lang=language[:2], slow=False)
            
            # Save to temporary file
            temp_path = output_path.replace('.wav', '_temp.mp3')
            tts.save(temp_path)
            
            # Convert MP3 to WAV and adjust speed
            audio = AudioSegment.from_mp3(temp_path)
            
            # Adjust speed if needed
            if speed != 1.0:
                # Change speed without changing pitch
                audio = audio._spawn(audio.raw_data, overrides={
                    "frame_rate": int(audio.frame_rate * speed)
                }).set_frame_rate(audio.frame_rate)
            
            # Export as WAV
            audio.export(output_path, format="wav")
            
            # Clean up temp file
            os.remove(temp_path)
            
            logger.info("GTTS synthesis completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"GTTS error: {e}")
            return False
    
    def _get_azure_voice_name(self, settings: Dict) -> str:
        """Get appropriate Azure voice name based on settings"""
        language = settings.get('VOICE_LANGUAGE', 'en-US')
        voice_type = settings.get('DEFAULT_VOICE', 'neural')
        
        # Neural voices for different languages
        neural_voices = {
            'en-US': 'en-US-AriaNeural',
            'en-GB': 'en-GB-SoniaNeural',
            'es-ES': 'es-ES-ElviraNeural',
            'fr-FR': 'fr-FR-DeniseNeural',
            'de-DE': 'de-DE-KatjaNeural',
            'it-IT': 'it-IT-ElsaNeural',
            'pt-BR': 'pt-BR-FranciscaNeural',
            'ja-JP': 'ja-JP-NanamiNeural',
            'ko-KR': 'ko-KR-SunHiNeural',
            'zh-CN': 'zh-CN-XiaoxiaoNeural',
        }
        
        return neural_voices.get(language, 'en-US-AriaNeural')
    
    def _create_ssml(self, text: str, settings: Dict) -> str:
        """Create SSML markup for advanced voice control"""
        voice_name = self._get_azure_voice_name(settings)
        speech_rate = settings.get('SPEECH_SPEED', 1.0)
        
        # Convert speed to percentage
        rate_percent = f"{int((speech_rate - 1.0) * 100):+d}%"
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice_name}">
                <prosody rate="{rate_percent}" pitch="+0%">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        return ssml
    
    async def get_available_voices(self) -> Dict:
        """Get list of available voices for the current TTS engine"""
        try:
            engine = self.tts_engine
            
            if engine == 'azure':
                return await self._get_azure_voices()
            elif engine == 'openai':
                return {
                    'voices': ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'],
                    'engine': 'openai'
                }
            elif engine == 'gtts':
                return {
                    'languages': ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh'],
                    'engine': 'gtts'
                }
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return {}
    
    async def _get_azure_voices(self) -> Dict:
        """Get available Azure voices"""
        try:
            speech_key = self.voice_settings.get('AZURE_SPEECH_KEY')
            speech_region = self.voice_settings.get('AZURE_SPEECH_REGION')
            
            if not speech_key or not speech_region:
                return {}
            
            # This would require additional Azure SDK calls
            # For now, return a predefined list
            return {
                'voices': [
                    'en-US-AriaNeural', 'en-US-JennyNeural', 'en-US-GuyNeural',
                    'en-GB-SoniaNeural', 'en-GB-RyanNeural',
                    'es-ES-ElviraNeural', 'fr-FR-DeniseNeural',
                    'de-DE-KatjaNeural', 'it-IT-ElsaNeural'
                ],
                'engine': 'azure'
            }
            
        except Exception as e:
            logger.error(f"Error getting Azure voices: {e}")
            return {}
    
    async def cleanup_old_audio_files(self, max_age_hours: int = 24):
        """Clean up old audio files to save storage space"""
        try:
            voice_dir = os.path.join(self.media_root, 'voice')
            if not os.path.exists(voice_dir):
                return
            
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(voice_dir):
                if filename.startswith('voice_') and filename.endswith('.wav'):
                    file_path = os.path.join(voice_dir, filename)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Cleaned up old audio file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up audio files: {e}")

# Singleton instance
voice_service = VoiceSynthesisService()