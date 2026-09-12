from backend.domain.comparison import compare
from backend.domain.errors import BusinessError
from backend.usecases.ports import Store


class Shopping:
    def __init__(self, store: Store):
        self.store = store

    def availability(self, data):
        items, suppliers, offers = self.store.catalog(data["items"], data.get("category_id"))
        return compare(items, suppliers, offers)["rows"]

    def comparison(self, data):
        items, suppliers, offers = self.store.catalog(data["items"])
        selected = [s for s in suppliers if s["id"] in data["supplier_ids"]]
        if len(selected) != len(data["supplier_ids"]):
            raise BusinessError("INVALID_SUPPLIER", "Selecione fornecedores ativos e existentes.")
        return compare(items, selected, offers)

    def save(self, user_id, data, list_id=None):
        return self.store.save_list(user_id, data, list_id)
