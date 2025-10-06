import time
import random
from dataclasses import dataclass
from typing import Callable

@dataclass
class CSMAConfig:
    """Configuración del protocolo CSMA"""
    slot_time: float = 0.000512      # 512 μs (estándar Ethernet)
    max_attempts: int = 16           # Intentos máximos
    persistence: float = 1.0         # 1-persistente
    jam_signal_time: float = 0.000032  # 32 μs

class CSMAProtocol:
    """Implementación mejorada del protocolo CSMA"""
    
    def __init__(self, config: CSMAConfig = None):
        self.config = config or CSMAConfig()
        self.stats = {
            'transmissions': 0,
            'collisions': 0,
            'successful': 0,
            'backoffs': 0
        }
    
    def transmit(self, transmit_callback: Callable, collision_callback: Callable = None) -> bool:
        """Ejecuta el algoritmo CSMA completo"""
        attempts = 0
        
        while attempts < self.config.max_attempts:
            attempts += 1
            self.stats['transmissions'] += 1
            
            # 1. Carrier Sense
            if not self.carrier_sense():
                self.stats['backoffs'] += 1
                wait_time = self.exponential_backoff(attempts)
                print(f"⏳ Backoff: esperando {wait_time*1000:.2f}ms")
                time.sleep(wait_time)
                continue
            
            # 2. Transmitir
            print("📤 Transmitiendo...")
            success = transmit_callback()
            
            if success:
                self.stats['successful'] += 1
                return True
            else:
                self.stats['collisions'] += 1
                if collision_callback:
                    collision_callback(attempts)
                
                # 3. Manejar colisión
                self.jam_signal()
                wait_time = self.exponential_backoff(attempts)
                time.sleep(wait_time)
        
        return False
    
    def carrier_sense(self, sense_time: float = 0.000096) -> bool:
        """Simula la detección de portadora"""
        time.sleep(sense_time)
        # En implementación real, aquí se verificaría el medio físico
        return random.random() > 0.3  # 70% de probabilidad de canal libre
    
    def exponential_backoff(self, attempt: int) -> float:
        """Backoff exponencial binario"""
        k = min(attempt, 10)
        slots = random.randint(0, 2**k - 1)
        return slots * self.config.slot_time
    
    def jam_signal(self):
        """Simula el envío de señal de jam"""
        print("🚨 Enviando señal jam")
        time.sleep(self.config.jam_signal_time)
    
    def get_stats(self):
        """Retorna estadísticas del protocolo"""
        efficiency = self.stats['successful'] / max(1, self.stats['transmissions'])
        return {**self.stats, 'efficiency': efficiency}