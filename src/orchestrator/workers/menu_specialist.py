from langchain_core.messages import SystemMessage
from src.orchestrator.state import DeliveryState
from src.orchestrator.tools.menu_tools import get_menu
from src.core.prompts import MENU_SPECIALIST_PROMPT
from typing import Dict, Any

def menu_specialist_node(state: DeliveryState) -> Dict[str, Any]:
    """
    Nodo especializado en consultas de menu.
    Accede a la herramienta get_menu, adjunta las instrucciones de ventas
    y ejecuta la respuesta en el estado para que el LLM la lea.
    """
    # llamamos la herramienta que conecta a RDS
    menu_information = get_menu.invoke({})

    # Combinamos el System Prompt de ventas con Datos de BD
    prompt_completo = f"{MENU_SPECIALIST_PROMPT}\n\n--- INFORMACIÓN DE LA BASE DE DATOS ---\n{menu_information}"
    
    # intectamos informacion como un mensaje de sistema en el estado
    # para que cuando usemos add_messages en el state, este mensaje se suma al historial
    return {
        "messages": [SystemMessage(content=prompt_completo)]
    }