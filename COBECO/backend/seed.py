from decimal import Decimal

from backend.adapters.database import Database
from backend.adapters.security import TokenSecurity
from backend.config import Settings

CATEGORIES = [
    "Supermercado",
    "Material de Construção",
    "Hardware e Informática",
    "Roupas e Calçados",
    "Lojas de Departamento",
]
PRODUCTS = [
    "Arroz 5 kg",
    "Feijão 1 kg",
    "Óleo de soja 900 ml",
    "Açúcar 1 kg",
    "Café 500 g",
    "Leite 1 L",
    "Farinha 1 kg",
    "Macarrão 500 g",
    "Sal 1 kg",
    "Produto sem oferta",
    "Martelo",
    "Alicate",
    "Chave de fenda",
    "Parafuso 10 un",
    "Furadeira",
    "Tinta branca 3 L",
    "Rolo de pintura",
    "Trena 5 m",
    "Fita isolante",
    "Luva de proteção",
    "Notebook i5",
    "Mouse USB",
    "Teclado USB",
    "Monitor 24 pol",
    "Cabo HDMI",
    "SSD 500 GB",
    "Memória 8 GB",
    "Webcam",
    "Headset",
    "Roteador",
    "Camiseta",
    "Calça jeans",
    "Tênis",
    "Meias 3 pares",
    "Jaqueta",
    "Boné",
    "Chinelo",
    "Camisa social",
    "Bermuda",
    "Cinto",
    "Toalha",
    "Lençol",
    "Panela",
    "Copo 6 un",
    "Prato 6 un",
    "Luminária",
    "Organizador",
    "Garrafa térmica",
    "Tapete",
    "Almofada",
]


def seed(database, settings):
    with database.transaction() as c:
        for index, name in enumerate(CATEGORIES, 1):
            c.execute(
                "INSERT INTO categories(id,name) VALUES (%s,%s) ON DUPLICATE KEY UPDATE name=%s",
                (index, name, name),
            )
        for index, name in enumerate(PRODUCTS, 1):
            c.execute(
                "INSERT INTO products(id,name,unit) VALUES (%s,%s,'un') ON DUPLICATE KEY UPDATE name=%s",
                (index, name, name),
            )
        for sid in range(1, 11):
            name = f"Fornecedor {chr(64 + sid)}"
            c.execute(
                "INSERT INTO suppliers(id,name,cnpj) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE name=%s",
                (sid, name, f"{sid:014d}", name),
            )
            for category in {(sid - 1) % 5 + 1, sid % 5 + 1}:
                c.execute(
                    "INSERT IGNORE INTO supplier_categories(supplier_id,category_id) VALUES (%s,%s)",
                    (sid, category),
                )
            for pid in range(1, 51):
                if pid == 10 or (sid + pid) % 5 >= 3:
                    continue
                price = (Decimal(5 + pid) * (Decimal("0.80") + Decimal(sid % 5) / 10)).quantize(
                    Decimal("0.01")
                )
                c.execute(
                    """INSERT INTO supplier_products(supplier_id,product_id,price,stock)
                    VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE price=%s,stock=%s""",
                    (sid, pid, price, 10 + pid % 20, price, 10 + pid % 20),
                )
        if settings.seed_demo_password:
            from backend.adapters.schemas import strong_password

            strong_password(settings.seed_demo_password)
            security = TokenSecurity(settings.jwt_secret)
            c.execute("SELECT id FROM users WHERE username='demo'")
            if not c.fetchone():
                c.execute(
                    """INSERT INTO users(username,name,email,password_hash,security_question,security_answer_hash)
                    VALUES ('demo','Usuário de demonstração','demo@example.com',%s,%s,%s)""",
                    (
                        security.hash(settings.seed_demo_password),
                        "Qual é o nome deste projeto?",
                        security.hash("cobeco"),
                    ),
                )


if __name__ == "__main__":
    settings = Settings()
    database = Database(settings)
    database.migrate()
    seed(database, settings)
    print("MySQL preparado: 5 categorias, 10 fornecedores, 50 produtos e 294 ofertas.")
