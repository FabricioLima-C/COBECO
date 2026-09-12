"""Extract the approved local prototype's markup/styles, excluding its demo business logic."""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "COBECO_figma_RF01_RF17_v2.html").read_text(encoding="utf-8")
css = re.search(r"<style>(.*?)</style>", source, re.S).group(1)
html = re.sub(r"<style>.*?</style>", '<link rel="stylesheet" href="/css/style.css">', source, flags=re.S)
html = re.sub(r"<script>.*?</script>", '<script type="module" src="/js/app.js"></script>', html, flags=re.S)

styles = {}


def extract_style(match):
    tag = match.group(0)
    style = re.search(r' style="([^"]*)"', tag)
    if not style:
        return tag
    name = "fig-" + hashlib.sha256(style.group(1).encode()).hexdigest()[:10]
    styles[name] = style.group(1)
    tag = tag.replace(style.group(0), "")
    if 'class="' in tag:
        tag = tag.replace('class="', f'class="{name} ', 1)
    else:
        tag = tag.replace(">", f' class="{name}">', 1)
    return tag


html = re.sub(r"<[a-zA-Z][^>]*>", extract_style, html)
html = html.replace('onclick="', 'data-action="').replace('oninput="', 'data-input-action="')
html = html.replace('value="Compras do mês"', 'value="" maxlength="100" placeholder="Ex.: Compras do mês"')
html = html.replace("Acesse suas listas e comparações salvas.", "Acesse e organize suas listas salvas.")
html = html.replace("comparar fornecedores e manter seu histórico de compras organizado.", "comparar fornecedores e manter suas compras organizadas.")
html = html.replace("Autenticação · estados 1–5", "Sua conta COBECO")
html = html.replace("Protótipo funcional COBECO", "Exemplo ilustrativo · catálogo de demonstração")
html = html.replace('<div id="listsWrap">', '<div class="panel-b no-print"><div class="field"><label for="savedQuery">Buscar por nome</label><input id="savedQuery" class="input" placeholder="Nome da lista"></div></div><div id="listsWrap">')
html = html.replace('<div class="range-row">', '<div class="field category-filter"><label for="category">Categoria do fornecedor</label><select id="category" class="select"><option value="">Todas as categorias</option></select></div><div class="range-row">')
html = html.replace('<div id="providerGrid"', '<div class="provider-tools"><span id="selectedCount" class="count"></span><button class="secondary" data-action="selectAll()">Selecionar todos</button><button class="ghost" data-action="clearSelection()">Limpar</button></div><div id="providerGrid"')
html = html.replace('<div class="row-actions">\n      <button class="secondary" data-action="closeConfirm()">', '<div id="confirmTyping" class="field hidden"><label for="confirmInput">Digite o nome para confirmar</label><input id="confirmInput" class="input"></div><div class="row-actions">\n      <button class="secondary" data-action="closeConfirm()">')
html = html.replace('<div id="modalback" class="modalback"', '<div id="modalback" role="dialog" aria-modal="true" aria-label="Entre para salvar sua lista" class="modalback"')
html = html.replace('<div id="confirmBack" class="modalback">', '<div id="confirmBack" role="dialog" aria-modal="true" aria-labelledby="confirmTitle" class="modalback">')
html = html.replace('<div class="modal">\n    <h2>Entre', '<div class="modal"><button class="modal-close" data-action="closeLoginModal()" aria-label="Fechar">×</button>\n    <h2>Entre')
html = html.replace('<div class="toast-wrap" id="toastWrap">', '<div class="toast-wrap" id="toastWrap" role="status" aria-live="polite">')
# Connect each existing label to its field without altering the prototype's visual structure.
html = re.sub(r'<label>(.*?)</label>(\s*<(?:input|select) id="([^"]+)")',
              lambda m: f'<label for="{m[3]}">{m[1]}</label>{m[2]}', html, flags=re.S)
html = html.replace('<link rel="stylesheet" href="/css/style.css">', '<link rel="stylesheet" href="/css/style.css"><link rel="stylesheet" href="/css/application.css">')
target = ROOT / "COBECO" / "frontend"
(target / "index.html").write_text(html, encoding="utf-8")
(target / "css" / "style.css").write_text(css + "\n" + "\n".join(f".{k}{{{v}}}" for k, v in styles.items()) + "\n", encoding="utf-8")
print("Figma HTML/CSS extracted; application behavior is provided exclusively by ES modules.")
