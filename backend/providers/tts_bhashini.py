import requests
import base64
import os
from .tts_base import TTSProvider

class BhashiniTTSProvider(TTSProvider):
    def __init__(self):
        self.user_id = os.environ.get("BHASHINI_USER_ID", "")
        self.api_key = os.environ.get("BHASHINI_API_KEY", "")
        self.pipeline_config_url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"

    def _get_pipeline_config(self, language: str):
        headers = {
            "userID": self.user_id,
            "ulcaApiKey": self.api_key
        }
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {
                            "sourceLanguage": language
                        }
                    }
                }
            ],
            "pipelineRequestConfig": {
                "pipelineId": "64392f96daac500b55c543cd"
            }
        }
        resp = requests.post(self.pipeline_config_url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def synthesize(self, text: str, language: str) -> bytes:
        try:
            config = self._get_pipeline_config(language)
            
            pipeline_resp = config.get("pipelineResponseConfig", [{}])[0]
            service_id = pipeline_resp.get("config", [{}])[0].get("serviceId")
            
            endpoint = config.get("pipelineInferenceAPIEndPoint", {})
            callback_url = endpoint.get("callbackUrl")
            inference_api_key = endpoint.get("inferenceApiKey", {}).get("value")

            if not inference_api_key:
                inference_api_key = os.environ.get("BHASHINI_INFERENCE_API_KEY")

            if not all([service_id, callback_url, inference_api_key]):
                raise ValueError("Incomplete pipeline config returned from Bhashini and no fallback INFERENCE key.")

            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {
                                "sourceLanguage": language
                            },
                            "serviceId": service_id,
                            "gender": "female"  # Assuming female voice by default, can be configurable
                        }
                    }
                ],
                "inputData": {
                    "input": [
                        {"source": text}
                    ]
                }
            }
            headers = {"Authorization": inference_api_key}
            resp = requests.post(callback_url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            
            audio_b64 = result.get("pipelineResponse", [{}])[0].get("audio", [{}])[0].get("audioContent", "")
            if not audio_b64:
                raise ValueError("No audio content returned from Bhashini.")
                
            return base64.b64decode(audio_b64)
            
        except Exception as e:
            print(f"Bhashini TTS Error: {e}")
            raise
