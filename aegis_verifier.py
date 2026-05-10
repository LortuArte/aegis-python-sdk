# ==============================================================================
# AEGIS POLICY GATE - LOCAL VERIFIER (ZERO-TRUST)
# ==============================================================================
# Este script permite la "Verificación Local" (Verify Locally) y el 
# "Zero-Trust Mirroring". 
# 
# Cualquier empresa, auditor o API puede usar este código para comprobar 
# matemáticamente que un recibo de AEGIS es auténtico, sin necesidad de 
# hacer llamadas a internet ni confiar en la base de datos de un tercero.
# ==============================================================================

import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

class AegisVerifier:
    def __init__(self, aegis_public_key_b64: str):
        """
        Inicializa el verificador usando SOLO la Clave Pública de AEGIS.
        (Esta es la clave que generaste y que es pública para todo el mundo).
        """
        # Limpiamos el prefijo si lo tiene
        if aegis_public_key_b64.startswith("ed25519:"):
            aegis_public_key_b64 = aegis_public_key_b64.split(":")[1]
            
        public_bytes = base64.b64decode(aegis_public_key_b64)
        self.public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)

    def verify_receipt_locally(self, receipt: dict) -> bool:
        """
        Toma el JSON (recibo) que emite AEGIS y comprueba su firma offline.
        """
        try:
            # 1. Extraer los datos del recibo
            agent_id = receipt.get("agent_did")
            operation = receipt.get("operation")
            amount = receipt.get("amount_usd")
            decision = receipt.get("policy_decision")
            signature_full = receipt.get("policy_signature", "")

            if not signature_full.startswith("ed25519:"):
                print("❌ FALSO: El recibo no tiene una firma Ed25519 válida.")
                return False

            # 2. Reconstruir el mensaje exacto que AEGIS firmó en el servidor
            # (Debe coincidir EXACTAMENTE con la línea 53 de tu server.py)
            expected_message = f"{agent_id}|{operation}|{amount}|{decision}".encode('utf-8')
            
            # 3. Extraer la firma en bytes
            signature_b64 = signature_full.split(":")[1]
            signature_bytes = base64.b64decode(signature_b64)

            # 4. Verificación Criptográfica Local (Cero Confianza / Zero-Trust)
            # Si la firma no coincide o alguien alteró 1 solo céntimo, esto fallará.
            self.public_key.verify(signature_bytes, expected_message)
            
            return True

        except InvalidSignature:
            print("❌ FRAUDE: La firma criptográfica no coincide. Datos alterados.")
            return False
        except Exception as e:
            print(f"❌ ERROR de validación: {e}")
            return False


# ==============================================================================
# EJEMPLO DE USO (Lo que usaría un auditor como Igor o un Vendedor)
# ==============================================================================
if __name__ == "__main__":
    
    # 1. La Clave Pública de AEGIS (La que pusiste en tu documentación)
    AEGIS_PUB_KEY = "PON_AQUI_TU_CLAVE_PUBLICA_BASE64_GENERADA_AYER"
    
    # 2. El recibo JSON que el Agente IA le entrega al Vendedor (Stripe/Rye)
    # Fíjate que esto lo recibe el vendedor sin hablar con AEGIS en ningún momento.
    recibo_sospechoso = {
        "agent_did": "did:key:langchain_test_agent",
        "operation": "qvac_inference",
        "amount_usd": "0.05",
        "policy_decision": "allow",
        "policy_signature": "ed25519:PON_AQUI_LA_FIRMA_QUE_TE_DEVUELVE_EL_SERVIDOR"
    }

    print("\n🔍 INICIANDO VERIFICACIÓN LOCAL (ZERO-TRUST)...")
    verificador = AegisVerifier(AEGIS_PUB_KEY)
    
    # Esta comprobación tarda 0.0001 segundos y no usa Internet.
    es_valido = verificador.verify_receipt_locally(recibo_sospechoso)
    
    if es_valido:
        print("✅ RECIBO AUTÉNTICO: Emitido por AEGIS L3. Seguro para procesar el pago.")
    else:
        print("⛔ RECIBO RECHAZADO: Posible falsificación o manipulación.")
