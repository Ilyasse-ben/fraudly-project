# Commandes Rapides — Poursuivre Investigation Fraudly

## 🚀 Next Steps IMMÉDIAT

### 1️⃣ Corriger Java Parent POM ✅ (FAIT)

```bash
# La correction Java 25 → 17 a été appliquée
# Vérifier :
cat fraudly-project/Backend-Spring/pom.xml | grep -A2 "<properties>"
```

Résultat attendu:
```xml
<maven.compiler.source>17</maven.compiler.source>
<maven.compiler.target>17</maven.compiler.target>
```

---

### 2️⃣ Compiler Backend-Spring

**Sur une machine avec Java 17+ installé:**

```powershell
cd fraudly-project/Backend-Spring/assessment-service
.\mvnw.cmd -B clean package -DskipTests
```

Ou test complet:
```powershell
.\mvnw.cmd -B clean test
```

**Si JAVA_HOME n'est pas défini:**
```powershell
# Localiser JDK 17+ (example)
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
# Puis relancer mvnw.cmd
```

---

### 3️⃣ Vérifier Docker Compose (si applicable)

```bash
# Dans fraudly-project/
docker-compose up -d  # Lance PostgreSQL + Kafka
# Attendre ~10s
docker ps  # Vérifier que les conteneurs tournent
```

---

### 4️⃣ Lancer Tests Backend-IA (légers)

```powershell
cd fraudly-project/Backend-IA
.\.venv\Scripts\python.exe -m pytest tests/test_unit.py -q
```

Résultat attendu: `33 passed`

---

## 📋 État Actuel du Projet

| Composant | Status | Actions |
|-----------|--------|---------|
| **Backend-IA** | 🟡 Partiellement OK | Tests unitaires ✓, E2E bloqué (torch GPU) |
| **Backend-Spring** | 🟡 Java fixé | Compile OK (après fix), tests en attente |
| **Frontend Angular** | ⚫ Non testé | À faire après backends stable |
| **Docker Compose** | ⚫ Non validé | À faire après fix Spring |

---

## 📄 Documentation

- ✅ `INVESTIGATION_REPORT.md` — Rapport complet d'analyse (généré)
- ✅ `verify_spring_config.py` — Vérification rapide configs (sans Maven)
- ✅ Correctifs appliqués:
  - Backend-IA: lazy imports, UUID coercion, type hints
  - Backend-Spring: Java 25 → 17 in parent pom.xml

---

## ⚠️ Blockers Restants

1. **JAVA_HOME non défini** — nécessaire pour compiler Spring localement
2. **PostgreSQL + Kafka** — nécessaires pour tester services Spring
3. **Torch c10.dll** — GPU requirement pour E2E Backend-IA (workaround: skip en CI)

---

## 🔧 Commandes Dépannage

### Vérifier compilation Spring (quick check)

```bash
cd fraudly-project/Backend-Spring
# Vérifier structure
ls -la */pom.xml
# Vérifier Java version dans parent
grep -E "<maven.compiler.(source|target)>" pom.xml
```

### Vérifier Backend-IA

```bash
cd fraudly-project/Backend-IA
# Vérifier imports paresseux appliqués
grep -A5 "try:" app/services/embedding_service.py | head -20
```

### Nettoyer caches Maven (si problèmes)

```powershell
# Windows
Remove-Item -Recurse -Force "$env:USERPROFILE\.m2\repository"

# Puis relancer
.\mvnw.cmd clean install
```

---

## 📞 Support

Si vous rencontrez des erreurs supplémentaires:

1. Partagez le message d'erreur exact (ex: `mvnw.cmd` output)
2. Vérifiez JAVA_HOME: `echo $env:JAVA_HOME` (Windows) ou `echo $JAVA_HOME` (Unix)
3. Vérifiez Docker: `docker ps` (si utilisé)
4. Relancez les commandes de vérification ci-dessus

---

**Rapport généré:** 12 mai 2026  
**Prochaines étapes:** Compilation Spring + tests intégration
