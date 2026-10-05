# Guía de migración SVN → Git

1. **Inventario:** repos, tamaño, binarios grandes (candidatos a Git LFS), usuarios activos.
2. **Mapa de autores:** `svn log -q | awk -F '|' '/^r/{print $2}' | sort -u` → `authors.txt` con `usuario = Nombre <email>`.
3. **Migración de prueba** con `svn-to-git.sh` en un entorno aislado.
4. **Validación:** número de commits, checksum del último árbol (`svn export` vs `git archive`), ramas y tags.
5. **Limpieza:** `git filter-repo` para remover secretos o binarios históricos (rotar toda credencial expuesta).
6. **Congelar SVN** (solo lectura) y migrar definitivamente; actualizar Jenkins/CI al nuevo origen.
7. **Adopción:** estrategia de ramas (trunk-based o GitFlow), protección de `main`, revisión por PR, capacitación al equipo.
8. **Rollback:** mantener SVN en solo lectura durante 30 días.
