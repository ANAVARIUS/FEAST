from langchain_core.messages import SystemMessage
from src.orchestrator.state import DeliveryState
from src.orchestrator.tools.menu_tools import get_menu
from typing import Dict, Any

def menu_specialist_node(state: DeliveryState) -> Dict[str, Any]:
    """
    Nodo especializado en consultas de menú.
    Accede a la herramienta get_menu e inyecta la respuesta en el estado.
    """
    # llamamos la herramienta que conecta a RDS
    menu_information = get_menu.invoke({})
    
    # intectamos informacion como un mensaje de sistema en el estado
    # para que cuando usemos add_messages en el state, este mensaje se suma al historial
    return {
        "messages": [SystemMessage(content=f"Información de la base de datos para el agente:\n{menu_information}")]
    }