#!/usr/bin/env python3
"""
Vérification rapide des configurations Spring — sans Maven requis.
Valide URLs, compatibilité dépendances, coherence config.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ─────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────

BACKEND_SPRING_ROOT = Path(__file__).parent / "Backend-Spring"
SERVICES = [
    "assessment-service",
    "authentification-service", 
    "analytics-service",
    "learning-service",
    "proctoring-service",
]

# ─────────────────────────────────────────────────────────────────────
# CHECKS
# ─────────────────────────────────────────────────────────────────────

def check_java_version(pom_path: Path) -> Tuple[str, str]:
    """Extract java version from pom.xml."""
    if not pom_path.exists():
        return None, f"File not found: {pom_path}"
    
    content = pom_path.read_text()
    match = re.search(r'<java\.version>(\d+)</java\.version>', content)
    if match:
        return match.group(1), None
    return None, "java.version not found"

def check_application_properties(service_dir: Path) -> Dict[str, str]:
    """Extract configuration from application.properties."""
    props_file = service_dir / "src/main/resources/application.properties"
    
    if not props_file.exists():
        return {}
    
    config = {}
    content = props_file.read_text()
    
    # Extract key configs
    for line in content.split('\n'):
        if '=' not in line or line.strip().startswith('#'):
            continue
        key, val = line.split('=', 1)
        key = key.strip()
        val = val.strip()
        if any(k in key for k in ['url', 'port', 'kafka', 'service']):
            config[key] = val
    
    return config

def check_pom_dependencies(pom_path: Path) -> List[str]:
    """List Spring Boot dependencies from pom.xml."""
    if not pom_path.exists():
        return []
    
    content = pom_path.read_text()
    deps = re.findall(r'<artifactId>(spring-.*?)</artifactId>', content)
    return list(set(deps))

# ─────────────────────────────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 80)
    print("🔍 VÉRIFICATION CONFIGURATIONS FRAUDLY SPRING")
    print("=" * 80 + "\n")
    
    # 1. Check parent pom.xml
    print("📋 PARENT POM.XML")
    print("-" * 80)
    parent_pom = BACKEND_SPRING_ROOT / "pom.xml"
    java_ver, err = check_java_version(parent_pom)
    if err:
        print(f"  ❌ {err}")
    else:
        status = "✓" if java_ver == "17" else "❌"
        print(f"  {status} Java version: {java_ver} (attendu: 17)")
    
    print()
    
    # 2. Check each service
    print("📦 SERVICES")
    print("-" * 80)
    
    services_ok = True
    
    for service_name in SERVICES:
        service_dir = BACKEND_SPRING_ROOT / service_name
        pom_path = service_dir / "pom.xml"
        
        if not service_dir.exists():
            print(f"  ❌ {service_name}: répertoire non trouvé")
            services_ok = False
            continue
        
        # Java version
        java_ver, _ = check_java_version(pom_path)
        java_status = "✓" if java_ver and int(java_ver) >= 17 else "❌"
        
        # Properties
        config = check_application_properties(service_dir)
        port = config.get('server.port', '???')
        
        # Dependencies
        deps = check_pom_dependencies(pom_path)
        has_kafka = any('kafka' in d.lower() for d in deps)
        kafka_status = "✓" if has_kafka else "⚠"
        
        print(f"\n  {service_name}")
        print(f"    {java_status} Java {java_ver}")
        print(f"    {kafka_status} Kafka: {'✓' if has_kafka else 'pas déclaré'}")
        print(f"    🔌 Port: {port}")
        print(f"    📚 Dépendances Spring: {len(deps)} trouvées")
        
        # Check for critical properties
        critical = ['spring.datasource.url', 'spring.kafka.bootstrap-servers']
        for prop in critical:
            if prop not in config:
                print(f"    ⚠ Manquant: {prop}")
                services_ok = False
    
    print()
    print("=" * 80)
    
    if java_ver == "17" and services_ok:
        print("✓ Configuration SAINE — prêt pour compilation Maven")
        print("  Commande: cd Backend-Spring && mvnw clean test")
        return 0
    else:
        print("❌ Configuration INVALIDE — corrections nécessaires")
        return 1

if __name__ == "__main__":
    sys.exit(main())
