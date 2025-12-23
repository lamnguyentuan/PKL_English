import sys
import os
import json
from dotenv import load_dotenv

# --- 1. SỬA LỖI PYTHON 3.13 (AUDIOOP) ---
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        pass # Sẽ báo lỗi ở pydub nếu không cài audioop-lts

import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

load_dotenv()

# --- 2. CẤU HÌNH ĐƯỜNG DẪN FFMPEG ---
# Lấy đường dẫn thư mục gốc của dự án (nơi chứa manage.py và ffmpeg.exe)
# Vì file này nằm trong thư mục 'speaking/', nên ta lấy cha của cha nó.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ffmpeg_path = os.path.join(BASE_DIR, "ffmpeg.exe")
ffprobe_path = os.path.join(BASE_DIR, "ffprobe.exe")

# Chỉ định tận tay cho pydub biết file thực thi nằm ở đâu
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

class AzureSpeechService:
    @staticmethod
    def assess_pronunciation(audio_file_path, reference_text):
        """
        Gửi file ghi âm và văn bản mẫu lên Azure để chấm điểm phát âm.
        Tự động convert sang chuẩn WAV 16kHz Mono bằng FFmpeg.
        """
        # --- 3. LẤY KEY TỪ .ENV ---
        subscription_key = os.getenv('AZURE_SPEECH_KEY')
        region = os.getenv('AZURE_SPEECH_REGION')

        if not subscription_key or not region:
            return {"success": False, "error": "Chưa cấu hình Azure Key/Region trong file .env"}

        # --- 4. CONVERT ÂM THANH SANG CHUẨN AZURE (WAV 16KHZ MONO) ---
        converted_path = audio_file_path + "_fixed.wav"
        try:
            # Pydub sẽ gọi ffmpeg.exe tại thư mục gốc để xử lý
            audio = AudioSegment.from_file(audio_file_path)
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(converted_path, format="wav")
            use_path = converted_path
        except Exception as e:
            print(f"Lỗi FFmpeg: {e}. Đang thử dùng file gốc...")
            use_path = audio_file_path

        # --- 5. GỌI API AZURE ---
        try:
            speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
            audio_config = speechsdk.audio.AudioConfig(filename=use_path)

            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                enable_miscue=True
            )

            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            pronunciation_config.apply_to(speech_recognizer)
            result = speech_recognizer.recognize_once_async().get()

            # --- 6. XỬ LÝ KẾT QUẢ TRẢ VỀ ---
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                response_json = json.loads(
                    result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
                )
                assessment_result = response_json['NBest'][0]['PronunciationAssessment']
                
                return {
                    "success": True,
                    "overall_score": assessment_result['PronScore'],
                    "accuracy_score": assessment_result['AccuracyScore'],
                    "fluency_score": assessment_result['FluencyScore'],
                    "completeness_score": assessment_result['CompletenessScore'],
                    "full_response": response_json['NBest'][0]
                }
            
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                return {"success": False, "error": f"Azure Error: {cancellation_details.error_details}"}
            else:
                return {"success": False, "error": "Không thể nhận diện giọng nói."}

        except Exception as e:
            return {"success": False, "error": f"Lỗi Python: {str(e)}"}
        
        finally:
            # Xóa file WAV tạm sau khi xong để tiết kiệm bộ nhớ
            if os.path.exists(converted_path):
                try:
                    os.remove(converted_path)
                except:
                    pass