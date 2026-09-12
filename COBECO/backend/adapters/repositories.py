from contextlib import contextmanager

from backend.domain.errors import BusinessError


def missing_list():
    return BusinessError("LIST_NOT_FOUND", "Lista não encontrada.", 404)


class UserTransaction:
    def __init__(self, cursor):
        self.cursor = cursor

    def user(self, *, username=None, user_id=None):
        field, value = ("id", user_id) if user_id is not None else ("username", username)
        self.cursor.execute(
            f"SELECT * FROM users WHERE {field}=%s AND deleted_at IS NULL FOR UPDATE", (value,)
        )
        return self.cursor.fetchone()

    def create_user(self, values):
        fields = ("username", "name", "email", "password_hash", "security_question", "security_answer_hash")
        self.cursor.execute(
            "INSERT INTO users (" + ",".join(fields) + ") VALUES (%s,%s,%s,%s,%s,%s)",
            tuple(values[f] for f in fields),
        )
        return self.user(user_id=self.cursor.lastrowid)

    def update_user(self, user_id, **values):
        allowed = {
            "name",
            "email",
            "password_hash",
            "refresh_hash",
            "session_version",
            "reset_hash",
            "reset_expires_at",
        }
        if not values or not set(values).issubset(allowed):
            raise ValueError("Invalid user update")
        self.cursor.execute(
            "UPDATE users SET " + ",".join(f"{f}=%s" for f in values) + " WHERE id=%s",
            (*values.values(), user_id),
        )
        return self.user(user_id=user_id)


class MySQLStore:
    def __init__(self, database):
        self.database = database

    @contextmanager
    def transaction(self):
        with self.database.transaction() as cursor:
            yield UserTransaction(cursor)

    def categories(self):
        with self.database.transaction() as c:
            c.execute("SELECT id,name,description FROM categories ORDER BY name")
            return c.fetchall()

    def products(self, query):
        # LIKE wildcards from the search term are treated as literal characters.
        query = query.replace("=", "==").replace("%", "=%").replace("_", "=_")
        with self.database.transaction() as c:
            c.execute(
                "SELECT id,name,unit FROM products WHERE active=1 AND name LIKE %s ESCAPE '=' "
                "ORDER BY name LIMIT 10",
                (f"%{query}%",),
            )
            return c.fetchall()

    @staticmethod
    def validate_items(c, items):
        ids = [i["product_id"] for i in items]
        placeholders = ",".join(["%s"] * len(ids))
        c.execute(
            f"SELECT id,name,unit FROM products WHERE active=1 AND id IN ({placeholders}) FOR SHARE", ids
        )
        products = {p["id"]: p for p in c.fetchall()}
        if len(products) != len(ids):
            raise BusinessError(
                "INVALID_PRODUCT", "Há produto repetido, inexistente ou indisponível na lista."
            )
        return [
            {**i, "name": products[i["product_id"]]["name"], "unit": products[i["product_id"]]["unit"]}
            for i in items
        ]

    def catalog(self, items, category_id=None):
        with self.database.transaction() as c:
            requested = self.validate_items(c, items)
            if category_id is not None:
                c.execute("SELECT id FROM categories WHERE id=%s", (category_id,))
                if not c.fetchone():
                    raise BusinessError("CATEGORY_NOT_FOUND", "Categoria não encontrada.", 404)
                c.execute(
                    """SELECT s.id,s.name FROM suppliers s JOIN supplier_categories sc
                    ON sc.supplier_id=s.id WHERE s.active=1 AND sc.category_id=%s ORDER BY s.name""",
                    (category_id,),
                )
            else:
                c.execute("SELECT id,name FROM suppliers WHERE active=1 ORDER BY name")
            suppliers = c.fetchall()
            ids = [i["product_id"] for i in items]
            c.execute(
                "SELECT supplier_id,product_id,price,stock,active FROM supplier_products "
                "WHERE product_id IN (" + ",".join(["%s"] * len(ids)) + ")",
                ids,
            )
            return requested, suppliers, c.fetchall()

    def lists(self, user_id, page, query):
        search = query.replace("=", "==").replace("%", "=%").replace("_", "=_")
        args = (user_id, f"%{search}%")
        where = "user_id=%s AND deleted_at IS NULL AND name LIKE %s ESCAPE '='"
        with self.database.transaction() as c:
            c.execute(f"SELECT COUNT(*) AS total FROM lists WHERE {where}", args)
            total = c.fetchone()["total"]
            page = min(page, max(1, (total + 19) // 20))
            c.execute(
                f"SELECT id,name,created_at,updated_at, "
                f"(SELECT COUNT(*) FROM list_items WHERE list_id=lists.id) AS item_count FROM lists WHERE {where} "
                "ORDER BY created_at DESC,id DESC LIMIT 20 OFFSET %s",
                (*args, (page - 1) * 20),
            )
            return {"items": c.fetchall(), "total": total, "page": page, "page_size": 20}

    @staticmethod
    def read_list(c, user_id, list_id, lock=False):
        c.execute(
            "SELECT id,name,created_at,updated_at FROM lists "
            "WHERE id=%s AND user_id=%s AND deleted_at IS NULL" + (" FOR UPDATE" if lock else ""),
            (list_id, user_id),
        )
        result = c.fetchone()
        if result is None:
            raise missing_list()
        c.execute(
            """SELECT li.product_id,li.quantity,p.name,p.unit,p.active FROM list_items li
            JOIN products p ON p.id=li.product_id WHERE li.list_id=%s ORDER BY li.id""",
            (list_id,),
        )
        result["items"] = c.fetchall()
        result["item_count"] = len(result["items"])
        return result

    def get_list(self, user_id, list_id):
        with self.database.transaction() as c:
            return self.read_list(c, user_id, list_id)

    def save_list(self, user_id, data, list_id=None):
        with self.database.transaction() as c:
            if list_id is not None:
                self.read_list(c, user_id, list_id, lock=True)
            self.validate_items(c, data["items"])
            if list_id is None:
                c.execute("INSERT INTO lists(user_id,name) VALUES (%s,%s)", (user_id, data["name"]))
                list_id = c.lastrowid
            else:
                c.execute(
                    "UPDATE lists SET name=%s,updated_at=UTC_TIMESTAMP(6) WHERE id=%s",
                    (data["name"], list_id),
                )
                c.execute("DELETE FROM list_items WHERE list_id=%s", (list_id,))
            c.executemany(
                "INSERT INTO list_items(list_id,product_id,quantity) VALUES (%s,%s,%s)",
                [(list_id, i["product_id"], i["quantity"]) for i in data["items"]],
            )
            return self.read_list(c, user_id, list_id)

    def delete_list(self, user_id, list_id):
        with self.database.transaction() as c:
            self.read_list(c, user_id, list_id, lock=True)
            c.execute("UPDATE lists SET deleted_at=UTC_TIMESTAMP(6) WHERE id=%s", (list_id,))
