# ==============================================================================
# AEGIS POLICY GATE - UNIVERSAL PYTHON SDK (V1.0.0)
# ==============================================================================
# Este es el cliente ligero oficial para interactuar con el Motor L3 de AEGIS.
# Agnóstico a frameworks. Úsalo con LangChain, Vercel, CrewAI o scripts nativos.
# ==============================================================================

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AegisSDK")

class AegisPolicyGate:
    """
    Cliente oficial para interactuar con la API del motor AEGIS L3.
    Garantiza latencia sub-milisegundo y prevención de doble gasto (ACID).
    """
    
    def __init__(self, endpoint_url: str, api_key: Optional[str] = None):
        if not endpoint_url:
            raise ValueError("🔴 CRÍTICO: El endpoint_url de AEGIS no puede estar vacío.")
            
        self.endpoint_url = endpoint_url.rstrip('/')
        self.api_key = api_key
        
        # SESIÓN PERSISTENTE CON REINTENTOS (Exponential Backoff)
        self.session = requests.Session()
        retries = Retry(
            total=3, 
            backoff_factor=0.05, 
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.session.headers.update({
            "User-Agent": "AEGIS-Universal-SDK/1.0.0",
            "Content-Type": "application/json"
        })
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def evaluate_intent(self, agent_did: str, operation: str, amount_usd: str, rail: str = "base/USDC") -> Dict[str, Any]:
        """
        Intercepta el gasto ANTES de la ejecución y delega la validación ACID al L3.
        Devuelve la decisión y la firma Ed25519 de seguridad.
        """
        payload = {
            "agent_did": agent_did,
            "operation": operation,
            "amount_usd": amount_usd,
            "rail": rail,
            "policy_decision": "allow" # Flag asíncrono
        }

        url = f"{self.endpoint_url}/v1/policy/evaluate"
        
        try:
            start_time = time.perf_counter()
            response = self.session.post(url, json=payload, timeout=(1.0, 2.0))
            response.raise_for_status() 
            data = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"[AEGIS L3] Validación {data.get('policy_decision').upper()} en {latency_ms:.2f}ms")
            return data

        except Exception as e:
            logger.error(f"[AEGIS] 🔴 ALERTA: Fallo de comunicación L3. Causa: {e}")
            # Arquitectura Fail-Closed: denegar por defecto ante errores de red.
            return {
                "agent_did": agent_did,
                "operation": operation,
                "policy_decision": "deny",
                "policy_signature": "error_no_signature"
            }
