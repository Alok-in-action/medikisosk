import requests
import base64
import os
from .asr_base import ASRProvider

class BhashiniASRProvider(ASRProvider):
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
                    "taskType": "asr",
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

    def transcribe(self, audio_path: str, language: str) -> str:
        try:
            config = self._get_pipeline_config(language)
            # Defensive fetching
            pipeline_resp = config.get("pipelineResponseConfig", [{}])[0]
            service_id = pipeline_resp.get("config", [{}])[0].get("serviceId")
            
            endpoint = config.get("pipelineInferenceAPIEndPoint", {})
            callback_url = endpoint.get("callbackUrl")
            inference_api_key = endpoint.get("inferenceApiKey", {}).get("value")

            if not inference_api_key:
                inference_api_key = os.environ.get("BHASHINI_INFERENCE_API_KEY")

            if not all([service_id, callback_url, inference_api_key]):
                raise ValueError("Incomplete pipeline config returned from Bhashini and no fallback INFERENCE key.")

            with open(audio_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "language": {
                                "sourceLanguage": language
                            },
                            "serviceId": service_id
                        }
                    }
                ],
                "inputData": {
                    "audio": [
                        {"audioContent": audio_b64}
                    ]
                }
            }
            headers = {"Authorization": inference_api_key}
            resp = requests.post(callback_url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            
            return result.get("pipelineResponse", [{}])[0].get("output", [{}])[0].get("source", "")
            
        except Exception as e:
            print(f"Bhashini ASR Error: {e}")
            raise
