"""
VERALLIA Modificator - Utilitaires XML
Fonctions pour modifier les fichiers XML Osmose
"""

from lxml import etree
import io


# ============================================================================
# NAMESPACE HR-XML
# ============================================================================

NAMESPACES = {
    'hr': 'http://ns.hr-xml.org/2004-08-02'
}


# ============================================================================
# LECTURE XML
# ============================================================================

def parse_xml(xml_content: bytes) -> etree._Element:
    """
    Parse un fichier XML en préservant l'encodage ISO-8859-1
    
    Args:
        xml_content: Contenu XML en bytes
        
    Returns:
        Arbre XML parsé
    """
    parser = etree.XMLParser(encoding='iso-8859-1', remove_blank_text=False)
    return etree.parse(io.BytesIO(xml_content), parser)


# ============================================================================
# EXTRACTION D'INFORMATIONS
# ============================================================================

def get_contract_info(tree: etree._Element) -> dict:
    """
    Extrait les informations du contrat XML
    
    Returns:
        dict avec les informations du contrat
    """
    root = tree.getroot()
    
    # Numéro de contrat
    contract_id = root.find('.//hr:AssignmentId/hr:IdValue', NAMESPACES)
    
    # Nom de la ressource
    given_name = root.find('.//hr:HumanResource//hr:GivenName', NAMESPACES)
    family_name = root.find('.//hr:HumanResource//hr:FamilyName', NAMESPACES)
    
    # CustomerJobCode actuel
    current_job_code = root.find('.//hr:CustomerJobCode', NAMESPACES)
    
    # Cycle horaire actuel
    current_cycle = root.find('.//hr:StaffingShift/hr:Id/hr:IdValue', NAMESPACES)
    
    return {
        'numeroContrat': contract_id.text if contract_id is not None else 'N/A',
        'ressource': f"{given_name.text if given_name is not None else ''} {family_name.text if family_name is not None else ''}".strip(),
        'customerJobCodeActuel': current_job_code.text if current_job_code is not None else '',
        'cycleHoraireActuel': {
            'name': current_cycle.get('name') if current_cycle is not None else '',
            'value': current_cycle.text if current_cycle is not None else ''
        }
    }


# ============================================================================
# MODIFICATION XML
# ============================================================================

def update_customer_job_code(tree: etree._Element, code_poste: str) -> bool:
    """
    Met à jour la balise <CustomerJobCode>
    
    Args:
        tree: Arbre XML
        code_poste: Nouveau code poste (ex: "4FACO2")
        
    Returns:
        True si modification réussie
    """
    root = tree.getroot()
    
    # Chercher la balise CustomerJobCode
    job_code_elem = root.find('.//hr:CustomerJobCode', NAMESPACES)
    
    if job_code_elem is None:
        print("⚠️ Balise CustomerJobCode introuvable")
        return False
    
    # Mettre à jour la valeur
    old_value = job_code_elem.text
    job_code_elem.text = code_poste
    
    print(f"✅ CustomerJobCode : '{old_value}' → '{code_poste}'")
    return True


def update_cycle_horaire(tree: etree._Element, code_cycle: str) -> bool:
    """
    Met à jour la balise <IdValue name="CYCLE">
    
    Args:
        tree: Arbre XML
        code_cycle: Nouveau code cycle (ex: "VA EQUIPE D 5X8")
        
    Returns:
        True si modification réussie
    """
    root = tree.getroot()
    
    # Chercher le bloc StaffingShift
    staffing_shift = root.find('.//hr:StaffingShift[@shiftPeriod="weekly"]', NAMESPACES)
    
    if staffing_shift is None:
        print("⚠️ Balise StaffingShift introuvable")
        return False
    
    # Chercher IdValue dans ce bloc
    id_value_elem = staffing_shift.find('.//hr:IdValue', NAMESPACES)
    
    if id_value_elem is None:
        print("⚠️ Balise IdValue introuvable dans StaffingShift")
        return False
    
    # Mettre à jour l'attribut name et la valeur
    old_name = id_value_elem.get('name', '')
    old_value = id_value_elem.text
    
    id_value_elem.set('name', 'CYCLE')
    id_value_elem.text = code_cycle
    
    print(f"✅ Cycle horaire : name='{old_name}' → 'CYCLE'")
    print(f"✅ Cycle horaire : '{old_value}' → '{code_cycle}'")
    return True


def apply_corrections(xml_content: bytes, code_poste: str, code_cycle: str) -> tuple[bytes, dict]:
    """
    Applique les corrections au XML
    
    Args:
        xml_content: Contenu XML original en bytes
        code_poste: Code du poste de travail
        code_cycle: Code du cycle horaire
        
    Returns:
        (xml_corrigé_bytes, dict_stats)
    """
    # Parser le XML
    tree = parse_xml(xml_content)
    
    stats = {
        'customerJobCode': False,
        'cycleHoraire': False
    }
    
    # Appliquer les corrections
    stats['customerJobCode'] = update_customer_job_code(tree, code_poste)
    stats['cycleHoraire'] = update_cycle_horaire(tree, code_cycle)
    
    # Convertir en bytes avec encodage ISO-8859-1
    output = io.BytesIO()
    tree.write(
        output,
        encoding='iso-8859-1',
        xml_declaration=True,
        pretty_print=False  # Préserver le formatage original
    )
    
    return output.getvalue(), stats


# ============================================================================
# VALIDATION
# ============================================================================

def validate_xml(xml_content: bytes) -> tuple[bool, str]:
    """
    Valide que le XML est bien formé
    
    Returns:
        (is_valid, error_message)
    """
    try:
        tree = parse_xml(xml_content)
        return True, "XML valide"
    except Exception as e:
        return False, str(e)


# ============================================================================
# COMPARAISON AVANT/APRÈS
# ============================================================================

def compare_xml(original: bytes, corrected: bytes) -> dict:
    """
    Compare le XML original et le XML corrigé
    
    Returns:
        dict avec les différences
    """
    original_tree = parse_xml(original)
    corrected_tree = parse_xml(corrected)
    
    original_info = get_contract_info(original_tree)
    corrected_info = get_contract_info(corrected_tree)
    
    return {
        'avant': original_info,
        'apres': corrected_info,
        'modifications': {
            'customerJobCode': original_info['customerJobCodeActuel'] != corrected_info['customerJobCodeActuel'],
            'cycleHoraire': original_info['cycleHoraireActuel'] != corrected_info['cycleHoraireActuel']
        }
    }
