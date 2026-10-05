#!/usr/bin/env bash
# Migra un repositorio SVN (layout estandar trunk/branches/tags) a Git conservando historial, autores, ramas y tags.
# Uso: ./svn-to-git.sh <svn-url> <authors.txt> <destino>
set -euo pipefail

SVN_URL="${1:?svn url}"
AUTHORS="${2:?archivo authors.txt (usuario_svn = Nombre <email>)}"
DEST="${3:?directorio destino}"

command -v git >/dev/null && git svn --version >/dev/null

git svn clone "$SVN_URL" --authors-file="$AUTHORS" --stdlayout --prefix=svn/ "$DEST"
cd "$DEST"

# SVN tags -> Git tags anotados
git for-each-ref --format='%(refname:short)' refs/remotes/svn/tags | while read -r ref; do
  tag="${ref#svn/tags/}"
  git tag -a "$tag" -m "Tag migrado desde SVN" "$ref"
  git branch -d -r "$ref" 2>/dev/null || true
done

# SVN branches -> ramas locales
git for-each-ref --format='%(refname:short)' refs/remotes/svn | grep -v -e '/tags/' -e '^svn/trunk$' | while read -r ref; do
  git branch "${ref#svn/}" "$ref"
done

git branch -m master main 2>/dev/null || true
git branch -m trunk main 2>/dev/null || true

echo "Validacion: commits migrados = $(git rev-list --all --count)"
echo "Siguiente: comparar con 'svn log | grep -c ^r[0-9]' y diff del ultimo checkout."
