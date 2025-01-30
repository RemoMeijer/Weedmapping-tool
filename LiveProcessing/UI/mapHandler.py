import json

class MapHandler:
    def __init__(self, data_base, backend):
        self.db = data_base
        self.backend = backend

    def goto_field_on_map(self, field_name):
        self.goto_field(field_name)

    def goto_field_on_map_from_run_tab(self, run_id):
        field = self.db.get_field_by_run_id(run_id)
        if field is not None:
            field_id = field.replace("Field_", "")
            self.goto_field(field_id)


    def goto_field(self, field_id):
        data = {
            "identifier": "field",  # Add an identifier
            "field_id": field_id  # Include the field ID
        }

        json_data = json.dumps(data)

        self.backend.send_data_to_js.emit(json_data)
