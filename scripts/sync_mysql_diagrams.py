"""Keep the MySQL DER and the duplicated diagram XML in Markdown synchronized."""
import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sql = (ROOT / "COBECO/backend/migrations/001_initial.sql").read_text(encoding="utf-8")
tables = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\) ENGINE=InnoDB;", sql, re.S)
positions = {"users": (40, 90), "lists": (510, 90), "list_items": (510, 410),
             "products": (510, 750), "suppliers": (1000, 90), "categories": (1470, 90),
             "supplier_categories": (1470, 440), "supplier_products": (1000, 700)}
doc = ET.Element("mxfile", host="app.diagrams.net", agent="COBECO MySQL", version="24.0.0")
diagram = ET.SubElement(doc, "diagram", id="cobeco-mysql", name="COBECO — DER MySQL")
model = ET.SubElement(diagram, "mxGraphModel", page="1", pageWidth="1980", pageHeight="1300", grid="1")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")


def cell(id, value, x, y, width, height, style):
    node = ET.SubElement(root, "mxCell", id=id, value=value, style=style, vertex="1", parent="1")
    ET.SubElement(node, "mxGeometry", x=str(x), y=str(y), width=str(width), height=str(height), **{"as": "geometry"})


cell("title", "<b>COBECO v3.1 — MySQL / InnoDB</b><br>8 tabelas de negócio · SQL parametrizado · transações · utf8mb4 · UTC",
     40, 10, 1880, 55, "text;html=1;align=center;fontSize=20;")
for name, body in tables:
    rows = [row.strip().rstrip(",") for row in body.strip().splitlines()]
    value = f"<b>{name}</b><hr>" + "<br>".join(html.escape(row) for row in rows)
    x, y = positions[name]
    color = "#FFEBEE" if name == "users" else "#E3F2FD" if name in {"lists", "list_items"} else "#E8F5E9"
    cell(name, value, x, y, 430, 45 + 23 * len(rows),
         f"rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacing=12;fillColor={color};fontSize=11;strokeColor=#557766;")

relations = [("users", "lists"), ("lists", "list_items"), ("products", "list_items"),
             ("suppliers", "supplier_products"), ("products", "supplier_products"),
             ("suppliers", "supplier_categories"), ("categories", "supplier_categories")]
for index, (source, target) in enumerate(relations):
    node = ET.SubElement(root, "mxCell", id=f"relation{index}", value="1 : N", edge="1", parent="1",
                         source=source, target=target,
                         style="edgeStyle=orthogonalEdgeStyle;html=1;startArrow=ERone;endArrow=ERmany;strokeColor=#226451;")
    ET.SubElement(node, "mxGeometry", relative="1", **{"as": "geometry"})
cell("notes", "<b>Notas</b><br>Categoria é filtro transitório de fornecedores (N:N). Produtos não têm categoria.<br>users contém estado mínimo de sessão e recuperação; comparações não são persistidas.<br>schema_migrations é uma tabela técnica adicional, fora das 8 tabelas de negócio.<br>Seed: 5 categorias, 10 fornecedores, 50 produtos, 20 vínculos, 294 ofertas.",
     40, 1050, 1880, 120, "rounded=1;whiteSpace=wrap;html=1;align=left;spacing=16;fillColor=#FFF7E8;fontSize=13;")
ET.indent(doc, space="  ")
xml = ET.tostring(doc, encoding="unicode")
(ROOT / "der.drawio").write_text(xml + "\n", encoding="utf-8")
der_md = """# DER — COBECO v3.1 / MySQL

Atualizado em 12/09/2026 conforme a decisão do usuário. Fonte executável: [001_initial.sql](COBECO/backend/migrations/001_initial.sql). O XML abaixo é gerado a partir desse schema por `scripts/sync_mysql_diagrams.py`.

- Oito tabelas de negócio; `schema_migrations` é a nona tabela física e controla versões.
- Sete FKs, cinco constraints UNIQUE além das PKs, seis CHECKs e duas PKs compostas.
- Soft delete em `users` e `lists`; itens exigem produto de catálogo e quantidade 1–9999.
- Categorias são N:N com fornecedores; preços/estoque também formam relação N:N fornecedor/produto.
- MySQL/InnoDB, moeda DECIMAL(12,2), utf8mb4 e timestamps UTC.
- `session_version`, `refresh_hash`, `reset_hash` e `reset_expires_at` suportam revogação e recuperação sem tabela de sessões/tokens.
- Categoria da lista é filtro transitório, não coluna persistida. Sem tabelas de comparação ou histórico.

## Diagrama editável

[Abrir arquivo Draw.io](der.drawio)

```xml
"""
(ROOT / "diagrama_DER.md").write_text(der_md + xml + "\n```\n", encoding="utf-8")

# Keep the approved use-case layout while fixing obsolete include/extend references.
uc = ET.parse(ROOT / "uc.drawio")
uc_root = uc.getroot().find(".//root")
for node in list(uc_root):
    if node.attrib.get("id") in {"inc13", "ext2"}:
        uc_root.remove(node)
    if node.attrib.get("id") in {"gen1", "leg2b"}:
        node.set("style", node.get("style", "").replace("dashed=1;", "dashed=0;"))
ET.indent(uc, space="  ")
uc_xml = ET.tostring(uc.getroot(), encoding="unicode")
(ROOT / "uc.drawio").write_text(uc_xml + "\n", encoding="utf-8")
analysis = ROOT / "analise_REQ_CasosDeUso.md"
text = analysis.read_text(encoding="utf-8-sig")
text = re.sub(r"```xml\s*.*?\s*```", lambda _: "```xml\n" + uc_xml + "\n```", text, flags=re.S)
analysis.write_text(text, encoding="utf-8")
print("MySQL DER and UC Markdown/XML synchronized.")
